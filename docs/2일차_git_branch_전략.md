# Git 브랜치 전략 정리

## 1. Git 브랜치란?

Git 브랜치는 하나의 프로젝트에서 서로 독립적인 작업 공간을 만드는 기능이다.

여러 명의 개발자가 같은 프로젝트를 작업할 때 각자 별도의 브랜치에서 기능을 개발하면 다른 개발자의 코드에 직접적인 영향을 주지 않고 작업할 수 있다.

기능 개발이 완료되면 커밋과 푸시를 진행하고, Pull Request와 코드 리뷰를 거쳐 기본 브랜치에 병합한다.

---

## 2. 브랜치 전략이란?

브랜치 전략은 브랜치의 종류와 역할, 생성 기준, 병합 순서 등을 정하여 저장소를 일관된 방식으로 운영하기 위한 워크플로우이다.

브랜치 전략이 필요한 이유는 다음과 같다.

- 개발자별 작업 내용을 독립적으로 관리할 수 있다.
- 여러 기능을 동시에 개발할 수 있다.
- 특정 기능이나 오류 수정 이력을 쉽게 추적할 수 있다.
- 검증되지 않은 코드가 배포 브랜치에 바로 반영되는 것을 방지할 수 있다.
- 팀원들이 동일한 규칙에 따라 협업할 수 있다.

대표적인 브랜치 전략으로는 Git Flow와 GitHub Flow가 있다.

---

## 3. Git Flow

Git Flow는 프로젝트의 개발, 배포 준비, 출시, 긴급 오류 수정을 여러 종류의 브랜치로 구분하여 관리하는 전략이다.

일반적으로 다음과 같은 브랜치를 사용한다.

### 3.1 main 브랜치

- 실제 배포 가능한 최종 상태의 코드를 관리한다.
- 운영 환경에 배포되는 안정적인 버전이 위치한다.
- 프로젝트에 따라 `master`라는 이름을 사용하기도 한다.

### 3.2 develop 브랜치

- 개발 중인 여러 기능을 통합하는 브랜치이다.
- 각각의 feature 브랜치에서 완성된 기능이 develop 브랜치로 병합된다.
- 다음 배포 버전에 포함될 기능들이 모이는 공간이다.

### 3.3 feature 브랜치

- 새로운 기능을 개발하기 위한 브랜치이다.
- 일반적으로 develop 브랜치에서 생성한다.
- 기능 개발이 완료되면 develop 브랜치로 Pull Request를 생성한다.

예시:

```text
feature/login
feature/create-user
feature/update-user
```

### 3.4 release 브랜치

- 배포를 준비하기 위한 브랜치이다.
- 새로운 기능 개발보다는 버그 수정, 버전 정보 변경, 배포 전 최종 점검 등을 수행한다.
- 배포 준비가 완료되면 main과 develop 브랜치에 병합한다.

### 3.5 hotfix 브랜치

- 운영 중인 서비스에서 발생한 긴급 오류를 수정하기 위한 브랜치이다.
- 일반적으로 main 브랜치에서 생성한다.
- 수정이 완료되면 main과 develop 브랜치에 모두 반영한다.

### 3.6 Git Flow의 일반적인 구조

```text
main
└── develop
    ├── feature/login
    ├── feature/create-user
    └── feature/update-user
```

기능 개발과 배포 과정은 다음과 같이 진행된다.

```text
develop에서 feature 브랜치 생성
→ 기능 개발
→ feature 브랜치를 develop에 병합
→ 배포 시 release 브랜치 생성
→ 최종 점검 후 main에 병합
→ 운영 중 긴급 오류 발생 시 hotfix 브랜치 생성
```

### 3.7 Git Flow의 장점

- 개발, 배포, 오류 수정 과정이 명확하게 구분된다.
- 배포 가능한 코드와 개발 중인 코드를 분리할 수 있다.
- 여러 버전을 동시에 관리하기 좋다.
- 대규모 프로젝트나 정기 배포 방식에 적합하다.
- 배포 안정성이 비교적 높다.

### 3.8 Git Flow의 단점

- 관리해야 하는 브랜치가 많다.
- 브랜치 생성과 병합 과정이 복잡하다.
- 작은 프로젝트에서는 불필요하게 무거운 전략이 될 수 있다.
- 빠르고 빈번한 배포에는 유연성이 떨어질 수 있다.

---

## 4. GitHub Flow

GitHub Flow는 main 브랜치와 작업 브랜치를 중심으로 운영하는 단순한 브랜치 전략이다.

새로운 기능 개발이나 오류 수정이 필요하면 main 브랜치에서 별도의 작업 브랜치를 생성한다.

작업이 완료되면 Pull Request를 생성하고, 코드 리뷰와 테스트를 거쳐 main 브랜치에 병합한다.

### 4.1 main 브랜치

- 배포 가능한 안정적인 코드를 관리한다.
- main 브랜치에 병합된 코드는 언제든 배포할 수 있는 상태를 유지하는 것이 원칙이다.

### 4.2 작업 브랜치

- 기능 추가, 오류 수정, 문서 작성 등의 작업을 수행한다.
- Git Flow의 feature 브랜치와 비슷한 역할을 한다.
- 작업 목적에 따라 다양한 이름을 사용할 수 있다.

예시:

```text
feat/create-user
fix/login-error
docs/update-readme
refactor/user-service
```

### 4.3 GitHub Flow의 일반적인 흐름

```text
main에서 작업 브랜치 생성
→ 기능 개발
→ 커밋 및 원격 저장소에 푸시
→ Pull Request 생성
→ 코드 리뷰 및 테스트
→ main에 병합
→ 필요 시 배포
```

예시:

```text
main
├── feat/create-user
├── fix/user-validation
└── docs/update-readme
```

### 4.4 GitHub Flow의 장점

- 브랜치 구조가 단순하다.
- 규칙을 이해하고 적용하기 쉽다.
- Pull Request 중심으로 협업할 수 있다.
- 기능 개발과 배포를 빠르게 진행할 수 있다.
- 소규모 팀이나 개인 프로젝트에 적합하다.

### 4.5 GitHub Flow의 단점

- 별도의 개발 통합 브랜치나 배포 준비 브랜치가 없다.
- main 브랜치 관리가 제대로 되지 않으면 안정성이 떨어질 수 있다.
- 여러 버전을 동시에 운영하기 어렵다.
- 충분한 코드 리뷰와 테스트 없이 병합하면 문제가 바로 main에 반영될 수 있다.

---

## 5. Git Flow와 GitHub Flow 비교

| 구분 | Git Flow | GitHub Flow |
|---|---|---|
| 기본 브랜치 | main, develop | main |
| 주요 작업 브랜치 | feature, release, hotfix | feature 또는 작업 목적별 브랜치 |
| 구조 | 복잡함 | 단순함 |
| 배포 방식 | 정기 배포에 적합 | 빠르고 잦은 배포에 적합 |
| 배포 안정성 | 비교적 높음 | 리뷰와 테스트 수준에 따라 달라짐 |
| 여러 버전 관리 | 적합함 | 상대적으로 어려움 |
| 적합한 프로젝트 | 대규모 프로젝트, 복잡한 서비스 | 소규모 팀, 개인 프로젝트, 과제 |
| 장점 | 역할과 배포 단계가 명확함 | 빠르고 이해하기 쉬움 |
| 단점 | 브랜치 관리가 복잡함 | 별도의 배포 준비 단계가 부족함 |

---

## 6. 과제 프로젝트에 적합한 전략

이번 과제 프로젝트에는 GitHub Flow가 더 적합하다고 판단한다.

그 이유는 다음과 같다.

- 소규모 팀으로 진행한다.
- 비교적 간단한 기능을 중심으로 개발한다.
- 과제 단위로 빠르게 작업하고 결과를 확인해야 한다.
- Git Flow의 release, hotfix 브랜치까지 운영하면 관리가 불필요하게 복잡해질 수 있다.
- Pull Request와 코드 리뷰를 중심으로 협업 과정을 연습할 수 있다.

따라서 기본적으로 다음과 같은 구조를 사용할 수 있다.

```text
main
└── feat/기능명
```

예시:

```text
main
├── feat/get-users
├── feat/create-user
├── feat/update-user
└── feat/delete-user
```

작업 순서는 다음과 같다.

```text
main 최신화
→ main에서 feature 브랜치 생성
→ 기능 개발
→ 커밋
→ 원격 저장소에 푸시
→ Pull Request 생성
→ 다른 팀원의 코드 리뷰
→ main에 병합
```

---

## 7. develop 브랜치를 함께 사용하는 경우

팀원별 기능을 바로 main에 병합하지 않고, 먼저 통합 테스트를 진행해야 한다면 develop 브랜치를 추가하여 운영할 수 있다.

```text
main
└── develop
    ├── feat/get-users
    ├── feat/create-user
    ├── feat/update-user
    └── feat/delete-user
```

이 경우 작업 브랜치는 develop에서 생성하고, Pull Request도 develop을 대상으로 생성한다.

```text
develop 최신화
→ develop에서 feature 브랜치 생성
→ 기능 개발
→ feature 브랜치를 develop에 병합
→ 통합 테스트
→ develop을 main에 병합
```

이 방식은 Git Flow의 일부 구조를 활용한 형태이며, 순수한 GitHub Flow보다는 브랜치가 하나 더 추가된 전략이다.

---

## 8. 팀 브랜치 운영 규칙 예시

### 8.1 브랜치 이름

```text
feat/기능명
fix/오류명
docs/문서명
refactor/대상명
```

예시:

```text
feat/create-user
fix/email-validation
docs/add-team-rule
refactor/user-router
```

### 8.2 Pull Request 방향

develop 브랜치를 사용하는 경우:

```text
feat/기능명 → develop
develop → main
```

develop 브랜치를 사용하지 않는 경우:

```text
feat/기능명 → main
```

### 8.3 기본 작업 순서

```bash
git switch develop
git pull origin develop
git switch -c feat/기능명
```

기능 개발 후:

```bash
git add .
git commit -m "feat: 기능 설명"
git push -u origin feat/기능명
```

그다음 GitHub에서 Pull Request를 생성하고 코드 리뷰 후 병합한다.

---

## 9. 결론

Git Flow는 브랜치별 역할이 명확하고 배포 안정성이 높아 대규모 프로젝트나 여러 버전을 운영하는 서비스에 적합하다.

반면 GitHub Flow는 구조가 단순하고 빠르게 기능을 개발하고 병합할 수 있어 소규모 팀, 개인 프로젝트, 과제 프로젝트에 적합하다.

이번 프로젝트에서는 GitHub Flow를 기본 전략으로 사용하는 것이 적절하다.

다만 팀원별 기능을 바로 main에 병합하지 않고 먼저 통합 테스트를 진행해야 한다면 develop 브랜치를 추가하여 프로젝트를 진행할 예정이다.

```text
feature 브랜치
→ develop 브랜치
→ main 브랜치
```

이 구조는 GitHub Flow의 단순함을 어느 정도 유지하면서 main 브랜치의 안정성을 높일 수 있다.