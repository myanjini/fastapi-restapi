# 부록 G. AWS 자원 정리 체크리스트

AWS 자원은 서로 기대어 있어서 아직 쓰이는 자원은 지울 수 없습니다. 그래서 "다른 것을 쓰는 쪽"부터 아래 순서로 지웁니다(16.9절). 16.10절에서 이 목록을 채우고, 18.11절에서 그대로 따라 지웁니다.

## 기본 정보

| 항목 | 내용 |
|---|---|
| 작성한 사람 |  |
| Owner 태그 값 |  |
| 작성한 날짜 |  |

## 정리 목록

| 순서 | 자원 | 이름 또는 ID | 계속 씀 | 삭제한 날 | 확인 방법 |
|---|---|---|---|---|---|
| 1 | ALB, 리스너, 대상 그룹 |  |  |  | aws elbv2 describe-load-balancers, describe-target-groups |
| 2 | EC2 인스턴스(EBS 포함) |  |  |  | aws ec2 describe-instances, describe-volumes |
| 3 | RDS 인스턴스, DB 서브넷 그룹, 수동 스냅샷 |  |  |  | aws rds describe-db-instances, describe-db-snapshots |
| 4 | ECR 저장소와 이미지 |  |  |  | aws ecr describe-repositories |
| 5 | S3 버킷(객체를 비운 뒤) |  |  |  | aws s3 ls |
| 6 | 탄력적 IP(쓴 경우) |  |  |  | aws ec2 describe-addresses |
| 7 | CloudWatch 로그 그룹, 경보, SNS 주제 |  |  |  | aws logs describe-log-groups, aws cloudwatch describe-alarms |
| 8 | Parameter Store 파라미터 |  |  |  | aws ssm describe-parameters |
| 9 | 보안 그룹, 서브넷, 라우팅 테이블, 인터넷 게이트웨이, VPC |  |  |  | aws ec2 describe-vpcs |
| 10 | IAM 역할(EC2, 배포), OIDC 공급자 |  |  |  | aws iam list-roles, list-open-id-connect-providers |
| 11 | 비용 확인 |  |  |  | Cost Explorer, Billing and Cost Management |

## 정리할 때 확인할 것

| 순서 | 확인 사항 |
|---|---|
| 1 | 리스너는 ALB와 함께 지워지고, 대상 그룹은 ALB가 완전히 지워진 뒤에 지울 수 있습니다. |
| 2 | 인스턴스를 종료한 뒤 EBS 볼륨이 남지 않았는지 확인합니다. "중지"는 삭제가 아닙니다. |
| 3 | 최종 스냅샷을 만들지 정한 뒤 삭제하고, 직접 만든 수동 스냅샷도 지웁니다. 운영 DB라면 최종 스냅샷을 반드시 남깁니다. |
| 4 | --force로 저장소 안의 이미지까지 함께 지웁니다. |
| 5 | 버킷은 객체를 모두 비워야 지워집니다. |
| 6 | 할당한 채 둔 탄력적 IP에는 요금이 붙습니다. |
| 7 | 보존 기간을 정했더라도 로그 그룹은 직접 지워야 사라집니다. |
| 8 | 실습용 파라미터는 이름 목록으로 한 번에 지웁니다. |
| 9 | 기본 VPC가 아닌지 확인하고 실습 VPC를 지웁니다. 의존 오류가 나면 아직 지워지는 중인 자원이 있는 것입니다. |
| 10 | 공용 계정에서 다른 사람도 쓰는 OIDC 공급자는 지우지 않습니다. GitHub 저장소의 배포 역할 변수도 함께 지웁니다. |
| 11 | 비용은 하루쯤 늦게 반영되므로 다음 날 다시 확인합니다. Owner 태그로 조회한 결과가 비어 있어야 합니다. |
