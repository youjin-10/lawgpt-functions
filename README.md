### 프로젝트 구조
카카오톡 채널에서 유저가 문의함 -> 채널톡 웹훅으로 azure functions에 요청(유저 메세지) 전송 -> Open AI API에 프롬프트 전송 -> Response를 받아 웹훅으로 답변 리턴
