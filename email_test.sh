# load tokens from .env file
export $(cat .env | xargs)

email=$1

if [ -z $email ]; then
    echo Email must not be empty. Please remember to pass email as argument!
    exit 1
fi

echo -e "sending request with your email: \"$email\"\n"

curl -H "token: $READ_TOKEN" -d "{\"domain\": \"andrewsblog.com\", \"email\": \"$email\"}" https://kpi.ndrew.me/api/statistics/visits/report
