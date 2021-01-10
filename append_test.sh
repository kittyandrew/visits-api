# load tokens from .env file
export $(cat .env | xargs)

echo -e "visiting many urls with single unque id..\n"
for i in {1..9}
do
    curl -H "token: $APPEND_TOKEN" -d "{\"domain\": \"andrewsblog.com\", \"path\": \"/my/cool/blog/1000${i}\", \"unique_id\": \"o1i24ci1v14vofvn\"}" https://kpi.ndrew.me/api/statistics/visits/new -w ""
    echo finished request \#$i!
done
echo -e "\nnow repeating some requests, to get repeated visits with new ids..\n"

for i in {1..4}
do 
    for x in $(seq 1 $i)
    do
        curl -H "token: $APPEND_TOKEN" -d "{\"domain\": \"andrewsblog.com\", \"path\": \"/my/cool/blog/1000${i}\", \"unique_id\": \"o1i24ci${i}v14vofvn\"}" https://kpi.ndrew.me/api/statistics/visits/new -w ""
        echo finished request \#$x with unique id \#$i!
    done
    echo -e "\nswitching to new unique id..\n"
done
echo -e "\nfinished adding more requests!\n"
