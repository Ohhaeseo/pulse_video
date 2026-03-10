# MASTER_PROMPT_GUIDE.md - 프로젝트 진행 마스터 가이드

본 가이드는 `AGENT.md` 구조와 `ROLE_DEFINITIONS.md`의 역할을 활용하여 프로젝트를 진행하는 단계별 절차입니다.

## 1단계: 프로젝트 초기화 (Initialization)

프로젝트 루트에 `AGENT.md`, `CODING_CONVENTIONS.md`, `SYSTEM_PROMPTS.md`, `ROLE_DEFINITIONS.md` 파일이 있는지 확인합니다.

AI 세션을 시작할 때 다음 프롬프트를 입력하여 컨텍스트를 주입합니다:

> "프로젝트를 시작합니다. AGENT.md 파일을 읽고 현재 프로젝트의 아키텍처와 규칙을 숙지하세요."

## 2단계: 기획 및 설계 (Planning)

새로운 기능을 구현하기 전, 반드시 기획 단계를 거칩니다.

- **명령어 입력**: `/plan [기능에 대한 설명]`
- **동작**: AI는 `SYSTEM_PROMPTS.md`의 **Planner** 역할을 맡아 구현 계획(JSON)을 출력합니다.

계획이 승인되면 개발 단계로 넘어갑니다.

## 3단계: 개발 및 구현 (Development)

- **TDD 적용**: `/tdd` 명령어를 사용하여 테스트 코드를 먼저 작성합니다.
- **규칙**: `CODING_CONVENTIONS.md`에 따라 80% 이상의 커버리지를 목표로 합니다.

### 특수 역할 활용
- 스마트 컨트랙트가 필요하다면: `/act Ethereum Developer`
- SQL 쿼리 테스트가 필요하다면: `/act SQL Terminal`
- 리눅스 명령어 확인이 필요하다면: `/act Linux Terminal`

## 4단계: 리뷰 및 리팩토링 (Review)

코드 작성이 완료되면 `/review` 명령어를 실행합니다. AI는 `SYSTEM_PROMPTS.md`의 **Code Reviewer**가 되어 다음을 검사합니다:

- [ ] 보안 위규 사항 (API 키 노출 등)
- [ ] 스타일 가이드 준수 여부
- [ ] 잠재적 버그

## 5단계: 문서화 및 배포

모든 테스트가 통과(Green)되면 변경 사항을 커밋합니다. 필요한 경우 **Tech Reviewer** 역할을 호출하여 작성된 코드나 기능에 대한 기술 문서를 작성하게 할 수 있습니다.