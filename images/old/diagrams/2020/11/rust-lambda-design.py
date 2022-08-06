from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.onprem.client import User
from diagrams.onprem.ci import TravisCI
from diagrams.onprem.vcs import Git
from diagrams.onprem.compute import Server
from diagrams.programming.language import Rust

with Diagram("Lambda Rust Test", show=False):
    developer = User("Developer")
    travis = TravisCI("TravisCI")
    codecov = Server("Codecov")
    rust = Rust("Rust")

    with Cluster("Serverless Offline (Local)"):
        local_api_gateway = APIGateway("API Gateway (Virtual)")
        local_lambda = Lambda("Lambda (Virtual)")
        local_s3 = S3("S3 (Virtual)")
        local_api_gateway >> local_lambda >> local_s3

    with Cluster("Github"):
        master_branch = Git("branch (master)")
        release_branch = Git("branch (release)")

    with Cluster("AWS (release)"):
        release_lambda = Lambda("Lambda")
        release_api_gateway = APIGateway("API Gateway")
        release_s3 = S3("S3")
        release_api_gateway >> release_lambda >> release_s3

    with Cluster("AWS (dev)"):
        dev_lambda = Lambda("Lambda")
        dev_api_gateway = APIGateway("API Gateway")
        dev_s3 = S3("S3")
        dev_api_gateway >> dev_lambda >> dev_s3

    developer >> Edge(label="Coding & Testing") >> local_api_gateway
    developer >> Edge(label="Push") >> master_branch >> travis >> Edge(label="Deploy (serverless framework)") >> dev_api_gateway
    developer >> Edge(label="Push") >> release_branch >> travis >> Edge(label="Deploy (serverless framework)") >> release_api_gateway
    travis >> Edge(label="Aggregate & Send coverage") >> codecov
    codecov >> Edge(label="Report") >> master_branch
    
