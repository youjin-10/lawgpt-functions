## 프로젝트 구조

카카오톡 채널에서 유저가 문의함 -> 채널톡 웹훅으로 azure functions에 요청(유저 메세지) 전송 -> Open AI API에 프롬프트 전송 -> API 응답값을 받아 채널톡 웹훅으로 답변 리턴

## 주요 파일
간단한 구조이기 때문에 [__init__.py](https://github.com/youjin-10/lawgpt-functions/blob/main/lawGptFunction/__init__.py)에 모든 코드가 있음
