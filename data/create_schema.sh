aws dynamodb create-table \
    --table-name IdeaBankUsers \
    --attribute-definitions \
        AttributeName=UserID,AttributeType=S \
        AttributeName=DisplayName,AttributeType=S \
    --key-schema AttributeName=UserID,KeyType=HASH AttributeName=DisplayName,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD \
    --endpoint-url http://localhost:8000

aws dynamodb create-table \
    --table-name Comment \
    --attribute-definitions \
        AttributeName=CommentID,AttributeType=S \
        AttributeName=CommentAuthor,AttributeType=S \
    --key-schema AttributeName=CommentID,KeyType=HASH AttributeName=CommentAuthor,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD \
    --endpoint-url http://localhost:8000

aws dynamodb create-table \
    --table-name Vote \
    --attribute-definitions \
        AttributeName=VoteID,AttributeType=S \
        AttributeName=VoteCaster,AttributeType=S \
    --key-schema AttributeName=VoteID,KeyType=HASH AttributeName=VoteCaster,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD \
    --endpoint-url http://localhost:8000

aws dynamodb create-table \
    --table-name IdeaPost \
    --attribute-definitions \
      AttributeName=IdeaPostID,AttributeType=S \
      AttributeName=IdeaAuthorID,AttributeType=S \
    --key-schema AttributeName=IdeaPostID,KeyType=HASH AttributeName=IdeaAuthorID,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD \
    --endpoint-url http://localhost:8000

aws dynamodb create-table \
    --table-name ProblemPost \
    --attribute-definitions \
      AttributeName=ProblemPostID,AttributeType=S \
      AttributeName=ProblemAuthorID,AttributeType=S \
    --key-schema AttributeName=ProblemPostID,KeyType=HASH AttributeName=ProblemAuthorID,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD \
    --endpoint-url http://localhost:8000
