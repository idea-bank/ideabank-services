aws dynamodb create-table \
    --table-name IdeaBankAccounts \
    --attribute-definitions \
        AttributeName=DisplayName,AttributeType=S \
    --key-schema AttributeName=DisplayName,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD \
    --endpoint-url=http://localhost:8000

#aws dynamodb create-table \
#    --table-name Comment \
#    --attribute-definitions \
#        AttributeName=CommentID,AttributeType=S \
#        AttributeName=CommentAuthor,AttributeType=S \
#    --key-schema AttributeName=CommentID,KeyType=HASH AttributeName=CommentAuthor,KeyType=RANGE \
#    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
#    --table-class STANDARD \
#    --endpoint-url http://localhost:8000

#aws dynamodb create-table \
#    --table-name Vote \
#    --attribute-definitions \
#        AttributeName=VoteID,AttributeType=S \
#        AttributeName=VoteCaster,AttributeType=S \
#    --key-schema AttributeName=VoteID,KeyType=HASH AttributeName=VoteCaster,KeyType=RANGE \
#    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
#    --table-class STANDARD \
#    --endpoint-url http://localhost:8000

aws dynamodb create-table \
    --table-name IdeaBankNodes \
    --attribute-definitions \
      AttributeName=NodeTitle,AttributeType=S \
      AttributeName=NodeAuthor,AttributeType=S \
    --key-schema AttributeName=NodeTitle,KeyType=HASH AttributeName=NodeAuthor,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD \
    --endpoint-url=http://localhost:8000
