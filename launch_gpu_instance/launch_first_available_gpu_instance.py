import argparse
import dataclasses
import json
import pathlib
import time

import boto3
import botocore.client
import botocore.exceptions

DEFAULT_AMI_NAME_PATTERN = (
    "Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)*"
)

SKIPPABLE_ERROR_CODES = frozenset(
    {
        "InsufficientInstanceCapacity",
        "InsufficientFreeAddressesInSubnet",
        "Unsupported",
        "VcpuLimitExceeded",
        "InstanceLimitExceeded",
    }
)


@dataclasses.dataclass(frozen=True)
class Target:
    region: str
    instance_type: str
    azs: tuple[str, ...]
    security_group_ids: tuple[str, ...]
    key_name: str
    ami_id: str
    ami_owner: str
    ami_name_pattern: str
    vpc_id: str
    volume_size_gb: int
    name: str


def build_target(raw: dict) -> Target:
    return Target(
        region=raw["region"],
        instance_type=raw["instance_type"],
        azs=tuple(raw.get("azs", [])),
        security_group_ids=tuple(raw["security_group_ids"]),
        key_name=raw["key_name"],
        ami_id=raw.get("ami_id", ""),
        ami_owner=raw.get("ami_owner", "amazon"),
        ami_name_pattern=raw.get("ami_name_pattern", DEFAULT_AMI_NAME_PATTERN),
        vpc_id=raw.get("vpc_id", ""),
        volume_size_gb=raw.get("volume_size_gb", 0),
        name=raw.get("name", "gpu-instance"),
    )


def load_targets(path: pathlib.Path) -> list[Target]:
    config = json.loads(path.read_text())
    defaults = config.get("defaults", {})
    return [build_target({**defaults, **raw}) for raw in config["targets"]]


def find_image(ec2: botocore.client.BaseClient, target: Target) -> dict:
    if target.ami_id:
        images = ec2.describe_images(ImageIds=[target.ami_id])["Images"]
    else:
        images = ec2.describe_images(
            Owners=[target.ami_owner],
            Filters=[
                {"Name": "name", "Values": [target.ami_name_pattern]},
                {"Name": "state", "Values": ["available"]},
                {"Name": "architecture", "Values": ["x86_64"]},
            ],
        )["Images"]
    if not images:
        raise LookupError(f"no ami found in {target.region}")
    return max(images, key=lambda image: image["CreationDate"])


def candidate_azs(ec2: botocore.client.BaseClient, target: Target) -> list[str]:
    offerings = ec2.describe_instance_type_offerings(
        LocationType="availability-zone",
        Filters=[{"Name": "instance-type", "Values": [target.instance_type]}],
    )["InstanceTypeOfferings"]
    offered = {offering["Location"] for offering in offerings}
    if not target.azs:
        return sorted(offered)
    return [az for az in target.azs if az in offered]


def find_subnet(ec2: botocore.client.BaseClient, az: str, vpc_id: str) -> str:
    filters = [{"Name": "availability-zone", "Values": [az]}]
    if vpc_id:
        filters.append({"Name": "vpc-id", "Values": [vpc_id]})
    subnets = ec2.describe_subnets(Filters=filters)["Subnets"]
    subnets.sort(
        key=lambda subnet: (
            not subnet["DefaultForAz"],
            not subnet["MapPublicIpOnLaunch"],
        )
    )
    return subnets[0]["SubnetId"] if subnets else ""


def launch(
    ec2: botocore.client.BaseClient, target: Target, image: dict, subnet_id: str
) -> str:
    params = {
        "ImageId": image["ImageId"],
        "InstanceType": target.instance_type,
        "KeyName": target.key_name,
        "SecurityGroupIds": list(target.security_group_ids),
        "SubnetId": subnet_id,
        "MinCount": 1,
        "MaxCount": 1,
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": target.name}],
            }
        ],
    }
    if target.volume_size_gb:
        params["BlockDeviceMappings"] = [
            {
                "DeviceName": image["RootDeviceName"],
                "Ebs": {
                    "VolumeSize": target.volume_size_gb,
                    "VolumeType": "gp3",
                    "DeleteOnTermination": True,
                },
            }
        ]
    return ec2.run_instances(**params)["Instances"][0]["InstanceId"]


def try_az(
    ec2: botocore.client.BaseClient, target: Target, image: dict, az: str
) -> str:
    subnet_id = find_subnet(ec2, az, target.vpc_id)
    if not subnet_id:
        print(f"{target.region} {az}: no subnet found, skipping")
        return ""
    print(f"{target.region} {az}: requesting {target.instance_type}")
    try:
        return launch(ec2, target, image, subnet_id)
    except botocore.exceptions.ClientError as error:
        code = error.response["Error"]["Code"]
        if code not in SKIPPABLE_ERROR_CODES:
            raise
        print(f"{target.region} {az}: {code}")
        return ""


def try_target(target: Target) -> str:
    ec2 = boto3.client("ec2", region_name=target.region)
    image = find_image(ec2, target)
    azs = candidate_azs(ec2, target)
    print(f"{target.region}: {target.instance_type} offered in {azs}")
    for az in azs:
        instance_id = try_az(ec2, target, image, az)
        if instance_id:
            print(f"launched {instance_id} ({target.instance_type}) in {az}")
            return instance_id
    return ""


def run_round(targets: list[Target]) -> str:
    for target in targets:
        instance_id = try_target(target)
        if instance_id:
            return instance_id
    return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="launch a gpu instance by trying region, az and instance type targets in priority order"
    )
    parser.add_argument("--config", type=pathlib.Path, required=True)
    parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="number of passes over the whole list, 0 retries until something launches",
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="seconds between passes"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = load_targets(args.config)
    attempt = 0
    while args.rounds == 0 or attempt < args.rounds:
        attempt += 1
        print(f"round {attempt}")
        if run_round(targets):
            return 0
        if args.rounds == 0 or attempt < args.rounds:
            print(f"no capacity, retrying in {args.interval}s")
            time.sleep(args.interval)
    print("no capacity in any target")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
