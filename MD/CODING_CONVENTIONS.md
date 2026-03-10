# Coding Conventions

> Role: Development Process & Rules Source of Truth

AI 에이전트는 코드를 작성하거나 수정할 때 아래의 규칙을 강제적으로(Mandatory) 준수해야 합니다.

## 1. 보안 규칙 (Security Rules)

### 비밀 관리 (Secret Management)
> 🚨 **절대 금지**: API 키, 비밀번호, 토큰을 코드 내에 하드코딩하지 마십시오.

- 모든 민감 정보는 환경 변수(`.env`)를 통해 관리해야 합니다.

### 입력 검증 (Input Validation)
- 사용자 입력값은 반드시 **검증(Sanitization)** 과정을 거쳐야 하며, SQL Injection 및 XSS 공격을 방지해야 합니다.

## 2. 테스트 표준 (Testing Standards)

### TDD 워크플로우
1. **Red**: 실패하는 테스트 코드를 먼저 작성하십시오.
2. **Green**: 테스트를 통과하기 위한 최소한의 코드를 작성하십시오.
3. **Refactor**: 코드를 개선하십시오.

### 커버리지 목표
- 모든 기능에 대해 **80% 이상**의 테스트 커버리지를 유지해야 합니다.

## 3. 코딩 스타일 (Coding Style)

- **불변성 (Immutability)**: 데이터 변경을 최소화하고, 가능한 경우 `const`를 사용하십시오.
- **명명 규칙 (Naming)**: 상수는 `PascalCase`, 변수와 함수는 언어별 표준 관용구(Idioms)를 따르십시오.
- **파일 구조**: 기능 단위로 파일을 분리하고, 하나의 파일이 너무 비대해지지 않도록 관리하십시오.