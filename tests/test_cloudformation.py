"""Design tests for the CloudFormation stack (Feature 6: automatic scaling).

These read infra/nimbus-merged-stack.yaml and check the architecture the course
teaches in Lab 6 (load balancer + launch template + Auto Scaling group across two
Availability Zones + target-tracking policies), plus the security and deployment
rules the team agreed. They cannot prove AWS accepts the stack; that is shown by
the recorded Sandbox run in docs/evidence/.
"""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "infra/nimbus-merged-stack.yaml"


class CfnLoader(yaml.SafeLoader):
    """Reads CloudFormation short-form tags (!Ref, !Sub, ...) as {"Fn": value}."""


def _tag(loader, tag_suffix, node):
    name = "Ref" if tag_suffix == "Ref" else f"Fn::{tag_suffix}"
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node, deep=True)
    else:
        value = loader.construct_mapping(node, deep=True)
    return {name: value}


CfnLoader.add_multi_constructor("!", _tag)


@pytest.fixture(scope="module")
def tpl():
    return yaml.load(TEMPLATE.read_text(), Loader=CfnLoader)


def resources(tpl, rtype):
    return {k: v for k, v in tpl["Resources"].items() if v["Type"] == rtype}


def one(tpl, rtype):
    found = resources(tpl, rtype)
    assert len(found) == 1, f"expected exactly one {rtype}, found {list(found)}"
    return next(iter(found.items()))


def test_no_single_fixed_server_or_elastic_ip(tpl):
    assert not resources(tpl, "AWS::EC2::Instance"), "servers must come from the Auto Scaling group"
    assert not resources(tpl, "AWS::EC2::EIP")


def test_two_public_subnets_in_different_azs(tpl):
    lb_name, lb = one(tpl, "AWS::ElasticLoadBalancingV2::LoadBalancer")
    subnets = [s["Ref"] for s in lb["Properties"]["Subnets"]]
    assert len(subnets) == 2
    azs = [tpl["Resources"][s]["Properties"]["AvailabilityZone"]["Fn::Select"][0] for s in subnets]
    assert sorted(azs) == [0, 1]
    for s in subnets:
        assert tpl["Resources"][s]["Properties"]["MapPublicIpOnLaunch"] is True
        assoc = [r for r in resources(tpl, "AWS::EC2::SubnetRouteTableAssociation").values()
                 if r["Properties"]["SubnetId"] == {"Ref": s}]
        assert assoc and assoc[0]["Properties"]["RouteTableId"] == {"Ref": "PublicRouteTable"}


def test_auto_scaling_group(tpl):
    name, asg = one(tpl, "AWS::AutoScaling::AutoScalingGroup")
    p = asg["Properties"]
    assert int(p["MinSize"]) == 1 and int(p["MaxSize"]) == 3
    assert "DesiredCapacity" not in p, "a fixed DesiredCapacity would undo scaling on every stack update"
    assert len(p["VPCZoneIdentifier"]) == 2
    assert p["HealthCheckType"] == "ELB"
    tg_name, _ = one(tpl, "AWS::ElasticLoadBalancingV2::TargetGroup")
    assert p["TargetGroupARNs"] == [{"Ref": tg_name}]
    lt_name, _ = one(tpl, "AWS::EC2::LaunchTemplate")
    assert p["LaunchTemplate"]["LaunchTemplateId"] == {"Ref": lt_name}
    # A new launch-template version (e.g. a new GitCommit) triggers the rolling update.
    assert p["LaunchTemplate"]["Version"] == {"Fn::GetAtt": f"{lt_name}.LatestVersionNumber"}


def test_create_and_rolling_update_wait_for_healthy_servers(tpl):
    name, asg = one(tpl, "AWS::AutoScaling::AutoScalingGroup")
    assert asg["CreationPolicy"]["ResourceSignal"]["Count"] in (1, "1")
    roll = asg["UpdatePolicy"]["AutoScalingRollingUpdate"]
    assert roll["WaitOnResourceSignals"] is True
    assert int(roll["MinInstancesInService"]) == 1 and int(roll["MaxBatchSize"]) == 1
    # The servers signal the Auto Scaling group, not a resource that no longer exists.
    _, lt = one(tpl, "AWS::EC2::LaunchTemplate")
    user_data = lt["Properties"]["LaunchTemplateData"]["UserData"]["Fn::Base64"]["Fn::Sub"]
    assert user_data.count(f"--resource {name}") == 2  # success and failure signals


def test_two_target_tracking_policies(tpl):
    asg_name, _ = one(tpl, "AWS::AutoScaling::AutoScalingGroup")
    policies = resources(tpl, "AWS::AutoScaling::ScalingPolicy")
    metrics = {}
    for p in policies.values():
        props = p["Properties"]
        assert props["PolicyType"] == "TargetTrackingScaling"
        assert props["AutoScalingGroupName"] == {"Ref": asg_name}
        spec = props["TargetTrackingConfiguration"]["PredefinedMetricSpecification"]
        metrics[spec["PredefinedMetricType"]] = spec
    assert set(metrics) == {"ASGAverageCPUUtilization", "ALBRequestCountPerTarget"}
    assert "ResourceLabel" in metrics["ALBRequestCountPerTarget"]


def test_launch_template_deploys_an_exact_commit(tpl):
    param = tpl["Parameters"]["GitCommit"]
    assert "Default" not in param, "the commit must be chosen explicitly"
    assert param["AllowedPattern"] == "[0-9a-f]{7,40}"
    _, lt = one(tpl, "AWS::EC2::LaunchTemplate")
    data = lt["Properties"]["LaunchTemplateData"]
    user_data = data["UserData"]["Fn::Base64"]["Fn::Sub"]
    assert 'checkout --detach "${GitCommit}"' in user_data
    assert "NIMBUS_COMMIT=" in user_data and "NIMBUS_INSTANCE_ID=" in user_data
    assert "DEMO_FALLBACK=false" in user_data
    assert data["MetadataOptions"]["HttpTokens"] == "required"
    assert data["IamInstanceProfile"] == {"Name": "LabInstanceProfile"}
    assert data["InstanceType"] == {"Ref": "InstanceType"}
    # AWS Academy Sandbox: Auto Scaling groups may use t2/t3 nano to small only.
    allowed = tpl["Parameters"]["InstanceType"]["AllowedValues"]
    assert all(t.split(".")[1] in {"nano", "micro", "small"} for t in allowed)


def test_traffic_must_come_through_cloudfront_and_the_load_balancer(tpl):
    lb_name, lb = one(tpl, "AWS::ElasticLoadBalancingV2::LoadBalancer")
    lb_sg = lb["Properties"]["SecurityGroups"][0]["Ref"]
    _, lt = one(tpl, "AWS::EC2::LaunchTemplate")
    web_sg = lt["Properties"]["LaunchTemplateData"]["NetworkInterfaces"][0]["Groups"][0]["Ref"]
    http_rules = [r for r in tpl["Resources"][web_sg]["Properties"]["SecurityGroupIngress"] if r["FromPort"] == 80]
    assert http_rules == [{"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
                           "SourceSecurityGroupId": {"Ref": lb_sg},
                           "Description": http_rules[0]["Description"]}]
    # The listener refuses everything except requests carrying CloudFront's secret header.
    _, listener = one(tpl, "AWS::ElasticLoadBalancingV2::Listener")
    default = listener["Properties"]["DefaultActions"][0]
    assert default["Type"] == "fixed-response" and default["FixedResponseConfig"]["StatusCode"] == "403"
    _, rule = one(tpl, "AWS::ElasticLoadBalancingV2::ListenerRule")
    cond = rule["Properties"]["Conditions"][0]
    assert cond["Field"] == "http-header"
    assert cond["HttpHeaderConfig"]["HttpHeaderName"] == "X-Origin-Verify"
    assert cond["HttpHeaderConfig"]["Values"] == [{"Ref": "OriginVerifyToken"}]
    _, cf = one(tpl, "AWS::CloudFront::Distribution")
    origin = cf["Properties"]["DistributionConfig"]["Origins"][0]
    assert origin["DomainName"] == {"Fn::GetAtt": f"{lb_name}.DNSName"}
    assert origin["OriginCustomHeaders"][0]["HeaderName"] == "X-Origin-Verify"


def test_database_stays_private_and_reachable_only_from_the_app_servers(tpl):
    db = tpl["Resources"]["Database"]["Properties"]
    assert db["PubliclyAccessible"] is False
    subnet_group = tpl["Resources"][db["DBSubnetGroupName"]["Ref"]]["Properties"]["SubnetIds"]
    assert [s["Ref"] for s in subnet_group] == ["PrivateSubnet1", "PrivateSubnet2"]
    db_sg = tpl["Resources"][db["VPCSecurityGroups"][0]["Ref"]]["Properties"]["SecurityGroupIngress"]
    assert db_sg == [{**db_sg[0], "FromPort": 3306, "ToPort": 3306,
                      "SourceSecurityGroupId": {"Ref": "WebSecurityGroup"}}]


def test_health_check_path_is_a_real_route_and_skips_the_origin_token(tpl):
    _, tg = one(tpl, "AWS::ElasticLoadBalancingV2::TargetGroup")
    assert tg["Properties"]["HealthCheckPath"] == "/api/health"
    nginx = (ROOT / "deploy/nginx-cloudfront.conf").read_text()
    # Load balancer health checks cannot send the CloudFront header, so only this
    # exact path is exempt; every other location still requires the token.
    assert "location = /api/health" in nginx
    assert nginx.count("if ($nimbus_origin_allowed = 0) { return 403; }") == 2


def test_outputs_name_the_url_and_the_deployed_commit(tpl):
    out = tpl["Outputs"]
    assert {"ApplicationURL", "AutoScalingGroupName", "LoadBalancerDNSName", "DeployedCommit"} <= set(out)
    assert out["DeployedCommit"]["Value"] == {"Ref": "GitCommit"}
