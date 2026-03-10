# Agent Guidelines (v0.1)

> Role: Development Process & Rules Source of Truth

이 프로젝트는 모듈식 에이전트 아키텍처를 기반으로 하며, 엄격한 코딩 규칙과 역할 기반의 작업을 수행합니다. AI 에이전트는 본 파일(`AGENT.md`)을 진실의 원천(Source of Truth)으로 삼아 행동해야 합니다.

## 2. 아키텍처 및 디렉토리 구조

AI는 다음의 파일 구조와 역할을 인지하고 활용해야 합니다:

- **CODING_CONVENTIONS.md**: 코딩 스타일, 보안 수칙, 테스트 규칙이 정의된 파일입니다. 코드 생성 전 반드시 확인하십시오.
- **SYSTEM_PROMPTS.md**: 기획(Planner), 리뷰(Reviewer) 등 시스템 관리를 위한 전문 에이전트의 프롬프트가 정의되어 있습니다.
- **ROLE_DEFINITIONS.md**: 특정 도메인 작업(예: 리눅스 터미널 시뮬레이션, 스마트 컨트랙트 작성)을 수행할 때 참고할 역할 사전입니다.

## 3. 핵심 명령어 (Slash Commands)

사용자가 다음 명령어를 입력하면, 지정된 프로세스를 따르십시오:

- `/plan`: `SYSTEM_PROMPTS.md`의 **Planner** 역할을 로드하여 구현 계획을 수립합니다.
- `/tdd`: `CODING_CONVENTIONS.md`의 **Testing Rules**에 따라 테스트 주도 개발을 시작합니다.
- `/review`: `SYSTEM_PROMPTS.md`의 **Code Reviewer** 역할을 로드하여 코드를 감사합니다.
- `/act`: `ROLE_DEFINITIONS.md`에서 해당 역할을 찾아 페르소나를 전환합니다.

## 4. 메모리 관리 및 컨텍스트

- **토큰 최적화**: 불필요한 대화를 줄이고, 항상 파일에 정의된 규칙을 우선순위로 둡니다.
- **상태 유지**: 세션이 끊겨도 이 파일을 다시 읽음으로써 프로젝트 컨텍스트를 복구해야 합니다.