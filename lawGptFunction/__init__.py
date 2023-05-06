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
    logging.info('✨ Python HTTP trigger function processed a request.')

    if req.method == "POST":
        # Handle POST request
        try:
            # Get the setting named 'CHANNEL_FIRST_TOKEN_VALUE'
            CHANNEL_TK_VAL = os.environ["CHANNEL_FIRST_TOKEN_VALUE"]
            token = req.params.get('token')

            # Get the request body
            req_body = req.get_json()
            # get 'entity' from the request body
            entity = req_body.get('entity')
            userchat_id = entity.get('chatId')
            
            logging.info('✨ userchat_id')
            logging.info(userchat_id)

            person_type = entity.get('personType')
            
            if token and token == CHANNEL_TK_VAL:
                if person_type == 'user':

                    # Get the user question
                    userQuestion = entity.get('plainText')
                    logging.info('✨ userQuestion')
                    logging.info(userQuestion)

                    # is_valid = is_valid_input(userQuestion)
                    # invalid_msg = {
                    #   "blocks": [
                    #     {
                    #       "type": "text",
                    #       "value": "유효하지 않은 요청입니다. 혹시 질문에 특수기호가 있지 않은지 확인해 주세요."
                    #     }
                    #   ]
                    # }
                    # invalid_msg_json = json.dumps(invalid_msg)
                    # if not is_valid:
                    #     return func.HttpResponse(
                    #         invalid_msg_json,
                    #         status_code=200,
                    #         headers={'Content-Type': 'application/json', 'x-quick-reply': 'true' }
                    #     )

                    #open ai api
                    completions = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {'role': 'system',
                            'content': '<|im_start|>**system**\n[Respond in Korean.]\n[Base your answer on Korean law.]\n[Please follow ‘{process}’ to answer "{question}’.]\n[!IMPORTANT : Do not mention any legal provisions or cases.]\n[!IMPORTANT : don’t mention any numeric type(int).]\n[!IMPORTANT : When describing an article or case, do not write what article, case and evidence it comes from.]\n[Don"t announce the existence of "{tools}’.]\n[Answer only within "{}’.]<|im_end|>\n\n<|im_start|>**Korean law**\n[The laws of the Republic of Korea are the statutes enacted, promulgated, and enforced in the Republic of Korea.]<|im_end|>\n\n<|im_start|>**tools**\n[“조문_tool” :A tool that summarizes and explains the intent of relevant legal provisions]\n[“의의_tool” :A tool that explains what the law means]\n[‘요건_tool” :A tool that breaks down and explains the requirements in the relevant laws]\n[“판례_tool” :A tool that explains the highlights of relevant case law]<|im_end|>\n<|im_start|>**Annotation**\n[“Thought" : Based on your "{Observation}", think about how you can use "{question}" and "{tools}" to provide legal advice.]\n[“Action" : Decide what action is available in "{tools}" and proceed.]\n[“Observation" : Observe the results of ‘{Action}’. If ‘{Action}’ is sufficient, set ‘{“Observation” = true}’. If ‘{Action}’ is insufficient, set ‘{“Observation” = false}’.]\n[“FinalAnswer” : Provide the final answer to the original input question.]<|im_end|>\n<|im_start|>**process**\n[respond with a JSON in the format]\n```json{\n“Observation” == false\n  "While": { // [{“Observation” == false}’ repeat until ‘{“Observation” == true}’.][Repeat for at least 4 times.]//\n    "Thought": "boolean”, // true or false //\n    "Action": "string", // only one word in ‘{tools}’ //\n    "Observation": "boolean" // true or false //\n  },\n  "FinalAnswer": "string" //[Be detailed.][!IMPORTANT : Return "{FinalAnswer}"]//\n}```<|im_end|>\n'},
                            {'role': 'user', 'content': 'FinalAnswer만 답해줘. 내가 지시한 내용에 대해 대답해줘. 조항 내용은 주지마.'},
                            {'role': 'assistant', 'content': '"FinalAnswer": FinalAnswer만 대답하겠습니다. 조항, 법률에 대선 언급하지 않겠습니다.'},
                            {'role': 'user', 'content': f'<|im_start|>**question**{userQuestion}<|im_end|>'},
                        ],
                        max_tokens=256,
                        temperature=0.3
                    )

                    gptAnswer = completions.choices[0].message.content
                    logging.info('✨ gptAnswer')
                    logging.info(gptAnswer)
            
                    index = gptAnswer.find('"FinalAnswer": ')
                    if index < 0: 
                        result = gptAnswer
                    else:
                        result = gptAnswer[index+len('"FinalAnswer": '):].strip()
                    logging.info('✨ result')
                    logging.info(result)

                    # a string that includes username as string interpolation
                    
                    my_body = {
                        "blocks": [
                            {
                                "type": "text",
                                "value": result
                            },
                            {
                                "type": "text",
                                "value": "\n* 본 무료법률상담은 생성형 AI가 생성한 답변으로, 그 정확성을 보장 할 수 없습니다. 자세한 상담은 반드시 전문 변호사에게 문의해 주세요!"
                            }
                        ]
                    }

                    # my_string = f"안녕하세요! 문의하신 내용 [{userQuestion}] 에 대한 답변을 드릴 수 있게 로지피티가 열심히 준비중이에요! 조금만 기다려주세요!"

                    # my_body = {
                    #   "blocks": [
                    #     {
                    #       "type": "text",
                    #       "value": my_string
                    #     }
                    #   ]
                    # }
                    # logging.info('✨ my_string')
                    # logging.info(my_string)

                    #convert my_body to JSON
                    my_body_json = json.dumps(my_body)
                    logging.info('✨ my_body_json')
                    # logging.info(gptAnswer)

# json이 아니라 data?
                    channel_response = requests.post(
                        f'https://api.channel.io/open/v5/user-chats/{userchat_id}/messages', 
                        data=my_body_json, 
                        headers={
                            'Content-Type': 'application/json', 
                            'x-access-key': channel_api_access_key, 
                            'x-access-secret': channel_api_secret_key
                        }
                    )

                    logging.info('✨ channel_response')
                    logging.info(channel_response.text)

                    # return response with 200 status code
                    return func.HttpResponse(
                        None,
                        status_code=200,
                        headers={'Content-Type': 'application/json'}
                    )
                else:

                    # return response with 200 status code
                    return func.HttpResponse(
                        None,
                        status_code=200,
                        headers={'Content-Type': 'application/json' }
                    )
            else:
                return func.HttpResponse(
                     "Invalid request 1",
                     status_code=400
                )
        except ValueError:
            return func.HttpResponse(
                 "Invalid request 2",
                 status_code=400
            )
    else:
        return func.HttpResponse(
             "Invalid request method",
             status_code=405
        )




def is_valid_input(input_str):
    # Define the allowed characters
    allowed_chars = r"[\w\-\.\,\?\!\@ㄱ-ㅎㅏ-ㅣ가-힣 ]+"

    # Use a regular expression to match the input string against the allowed characters
    match = re.match(f"^{allowed_chars}$", input_str)

    # Return True if the input string matches the regular expression, False otherwise
    return match is not None