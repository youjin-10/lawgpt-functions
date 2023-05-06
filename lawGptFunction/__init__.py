import logging
import json
import os
import azure.functions as func
import re
import openai
import requests

openai.api_key = os.environ["OPEN_AI_API_KEY"]
channel_api_access_key = os.environ["CHANNEL_ACCESS_KEY"]
channel_api_secret_key = os.environ["CHANNEL_ACCESS_SECRET"]


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("✨ Python HTTP trigger function processed a request.")

    if req.method == "POST":
        return handle_post_request(req)
    else:
        return invalid_request_method_response()


def handle_post_request(req: func.HttpRequest):
    try:
        # Get the setting named 'CHANNEL_FIRST_TOKEN_VALUE'
        CHANNEL_TK_VAL = os.environ["CHANNEL_FIRST_TOKEN_VALUE"]
        token = req.params.get("token")

        if token and token == CHANNEL_TK_VAL:
            req_body = req.get_json()
            entity = req_body.get("entity")
            userchat_id = entity.get("chatId")
            person_type = entity.get("personType")

            logging.info(f"✨ userchat_id: {userchat_id}")

            if person_type == "user":
                gpt_answer, result = generate_gpt_answer(req_body)

                if result:
                    send_channel_response(userchat_id, result)
                    return success_response()
                else:
                    return invalid_request_response("Invalid request 1")
            else:
                return success_response()

        else:
            return invalid_request_response("Invalid request 1")
    except ValueError:
        return invalid_request_response("Invalid request 2")


def generate_gpt_answer(req_body):
    userQuestion = req_body.get("entity").get("content")
    completions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": '<|im_start|>**system**\n[Respond in Korean.]\n[Base your answer on Korean law.]\n[Please follow ‘{process}’ to answer "{question}’.]\n[!IMPORTANT : Do not mention any legal provisions or cases.]\n[!IMPORTANT : don’t mention any numeric type(int).]\n[!IMPORTANT : When describing an article or case, do not write what article, case and evidence it comes from.]\n[Don"t announce the existence of "{tools}’.]\n[Answer only within "{}’.]<|im_end|>\n\n<|im_start|>**Korean law**\n[The laws of the Republic of Korea are the statutes enacted, promulgated, and enforced in the Republic of Korea.]<|im_end|>\n\n<|im_start|>**tools**\n[“조문_tool” :A tool that summarizes and explains the intent of relevant legal provisions]\n[“의의_tool” :A tool that explains what the law means]\n[‘요건_tool” :A tool that breaks down and explains the requirements in the relevant laws]\n[“판례_tool” :A tool that explains the highlights of relevant case law]<|im_end|>\n<|im_start|>**Annotation**\n[“Thought" : Based on your "{Observation}", think about how you can use "{question}" and "{tools}" to provide legal advice.]\n[“Action" : Decide what action is available in "{tools}" and proceed.]\n[“Observation" : Observe the results of ‘{Action}’. If ‘{Action}’ is sufficient, set ‘{“Observation” = true}’. If ‘{Action}’ is insufficient, set ‘{“Observation” = false}’.]\n[“FinalAnswer” : Provide the final answer to the original input question.]<|im_end|>\n<|im_start|>**process**\n[respond with a JSON in the format]\n```json{\n“Observation” == false\n  "While": { // [{“Observation” == false}’ repeat until ‘{“Observation” == true}’.][Repeat for at least 4 times.]//\n    "Thought": "boolean”, // true or false //\n    "Action": "string", // only one word in ‘{tools}’ //\n    "Observation": "boolean" // true or false //\n  },\n  "FinalAnswer": "string" //[Be detailed.][!IMPORTANT : Return "{FinalAnswer}"]//\n}```<|im_end|>\n',
            },
            {"role": "user", "content": "FinalAnswer만 답해줘. 내가 지시한 내용에 대해 대답해줘. 조항 내용은 주지마."},
            {
                "role": "assistant",
                "content": '"FinalAnswer": FinalAnswer만 대답하겠습니다. 조항, 법률에 대선 언급하지 않겠습니다.',
            },
            {"role": "user", "content": f"<|im_start|>**question**{userQuestion}<|im_end|>"},
        ],
        max_tokens=256,
        temperature=0.3,
    )

    gpt_answer = completions.choices[0].message.content
    logging.info(f"✨ gptAnswer: {gpt_answer}")

    index = gpt_answer.find('"FinalAnswer": ')

    if index < 0:
        result = gpt_answer
    else:
        result = gpt_answer[index + len('"FinalAnswer": ') :].strip()

    logging.info(f"✨ result: {result}")

    return gpt_answer, result


def send_channel_response(userchat_id, result):
    message_body = create_message_body(result)
    message_body_json = json.dumps(message_body)
    logging.info(f"✨ message_body_json: {message_body_json}")

    channel_response = requests.post(
        f"https://api.channel.io/open/v5/user-chats/{userchat_id}/messages",
        data=message_body_json,
        headers={
            "Content-Type": "application/json",
            "x-access-key": channel_api_access_key,
            "x-access-secret": channel_api_secret_key,
        },
    )

    logging.info(f"✨ channel_response: {channel_response.text}")


def create_message_body(result):
    return {
        "blocks": [
            {"type": "text", "value": result},
            {
                "type": "text",
                "value": "\n* 본 무료법률상담은 생성형 AI가 생성한 답변으로, 그 정확성을 보장 할 수 없습니다. 자세한 상담은 반드시 전문 변호사에게 문의해 주세요!",
            },
        ]
    }


def success_response():
    return func.HttpResponse(None, status_code=200, headers={"Content-Type": "application/json"})


def invalid_request_response(message):
    return func.HttpResponse(message, status_code=400)


def invalid_request_method_response():
    return func.HttpResponse("Invalid request method", status_code=405)


def is_valid_input(input_str):
    # Define the allowed characters
    allowed_chars = r"[\w\-\.\,\?\!\@ㄱ-ㅎㅏ-ㅣ가-힣 ]+"

    # Use a regular expression to match the input string against the allowed characters
    match = re.match(f"^{allowed_chars}$", input_str)

    # Return True if the input string matches the regular expression, False otherwise
    return match is not None
