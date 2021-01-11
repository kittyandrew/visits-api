from aio_pika import connect_robust, Message
from validate_email import validate_email
from sanic.response import json, empty
from sanic import Sanic
import datetime
import logging
import ujson
import os
from .utils import verify


# CONFIG
APPEND_TOKEN     = os.environ["APPEND_TOKEN"]   # has only append rights to the data
READ_TOKEN       = os.environ["READ_TOKEN"]     # has read access to the data
RABBITMQ_HOST    = os.environ.get("RABBITMQ_HOST", "kpi-rabbitmq")
RABBITMQ_USER    = os.environ.get("RABBITMQ_USER", "rabbit")
RABBITMQ_PASS    = os.environ.get("RABBITMQ_PASS", "password")

app = Sanic(name="gateway")


@app.route("/api/statistics/visits/new", methods=["POST"])
async def api_statistics_visits_new(request):
    # authorization API token
    token = request.headers.get("token")
    if not token or token != APPEND_TOKEN:
        return json({"code": 1001, "message": f"Token \"{token}\" is invalid!"}, status = 403)

    # verifying arguments
    data = request.json
    if not data or not isinstance(data, dict):
        return json({"code": 1002, "message": f"Expected json, got \"{data}\""}, status = 403)
    
    # visited path argument
    path, err = verify(data, "path", str, max_len=255)
    if path is None:
        return err

    # visited domain name
    domain, err = verify(data, "domain", str, max_len=64)
    if domain is None:
        return err

    # unique session id
    unique_id, err = verify(data, "unique_id", str, min_len=12, max_len=32)
    if unique_id is None:
        return err

    # create current date here, before adding to the queue
    curr_date = datetime.datetime.now().isoformat()

    # encapsulate data
    data = {
        "date": curr_date,
        "domain": domain,
        "path": path,
        "unique_id": unique_id,
    }

    # send to the queue
    await app.rabbitmq.default_exchange.publish(
        Message(ujson.dumps(data).encode()),
        routing_key = "statistics_visits_new"
    )
    return empty(status = 200)


@app.route("/api/statistics/visits/report", methods=["POST"])
async def api_statistics_visits_report(request):
    # authorization API token for user
    token = request.headers.get("token")
    if not token or token != READ_TOKEN:
        return json({"code": 1001, "message": f"Token \"{token}\" is invalid!"}, status = 403)

    # verifying arguments
    data = request.json
    if not data or not isinstance(data, dict):
        return json({"code": 1002, "message": f"Expected json, got \"{data}\""}, status = 403)

    # domain to check stats for
    domain, err = verify(data, "domain", str, max_len=64)
    if not domain:
        return err

    # email to send statistics to
    email, err = verify(data, "email", str, max_len=128)
    if not email:
        return err

    # verify email (using module 'py3-validate-email')
    #     - checking with both regex and SMTP HELO request
    # TODO: it is definitely slow + sync (blocking)
    #       so, redo SMTP HELO check from scratch with async lib (aiosmtplib)
    verified = validate_email(email_address=email, check_regex=True, check_mx=True)
    if not verified:
        return json(
            {
                "code": 3001, 
                "message": f"Could not validate your email (\"{email}\")! " \
                            "Please make sure you entered a valid email.",
            },
            status = 403
        )

    # encapsulate data
    data = {
        "domain": domain,
        "email": email,
    }

    # send to the queue
    await app.rabbitmq.default_exchange.publish(
        Message(ujson.dumps(data).encode()),
        routing_key = "statistics_report"
    )
    return json(
        {
            "code": 2000,
            "message": "Your report will arrive shortly!"
        },
        status = 200
    )


@app.route("/", methods=["GET"])
async def route_hello(request):
    return json({"code": 1, "message": "Hello from KPI-LAB7 API!"})


@app.listener("before_server_start")
async def setup_rabbitmq_connection(app, loop):
    app.rabbitmq_con = await connect_robust(f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}")
    app.rabbitmq = await app.rabbitmq_con.channel()


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    app.run(host="0.0.0.0", port="8080", debug=False)
