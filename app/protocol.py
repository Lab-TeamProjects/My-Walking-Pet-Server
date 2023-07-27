OK = 'S00'                          # 성공

NOT_FOUND_EMAIL = "A01"             # 로그인 중 DB에서 이메일을 찾을 수 없을때
NOT_AUTH_EMAIL = "A02"              # 로그인 중 인증받지 않은 이메일 일때
NOT_CORRECT_PASSWORD = "A03"        # 올바르지 않은 비밀번호 일 때
EMAIL_IS_DUPLICATION = "A04"        # 이메일이 중복 되었을 때
EMAIL_SEND_FAIL = "A05"             # 인증 메일 전송 실패
INVALID_ACCESS_TOKEN = "A06"        # 유효하지않은 엑세스 토큰
NOT_AUTH_PASSWORD_RESET = "A07"
EXPIRED_ACCESS_TOKEN = "A08"        # 만료된 엑세스 토큰

INVALID_IMAGE_DATA = "D01"          # 잘못된 이미지 파일
UNCORRECTABLE_DATA = "D02"          # 수정할 수 없는 데이터
INVALUD_DATE = "D03"                # 유효하지 않은 날짜
INVALUD_DATE_RANGE = "D04"          # 잘못된 날짜 범위
NOT_USER = "D05"                    # 없는 유저
NOT_FOUND_PROFILE = "D06"           # 프로필 없음
MYSELF_AN_ETERNAL_FRIEND = "D07"    # 자기 자신 친구추가
INVALID_ITEM_ID = "D08"             # 알 코드 잘못됨
NO_MONEY = "D09"                    # 잔액 부족
NO_EGG = "D10"                      # 알이 없는데 사용하려고 함
SHORTFALL_VALUE = "D11"             # 수치 부족
NOT_FOUND_PROFILE_PHOTO = "D12"     # 프로필 사진 없음

NOT_MY_PET = "P01"                  # 자기 자신의 동물이 아님

FAIL = 'F00'
DATABASE_ERROR = 'F01'