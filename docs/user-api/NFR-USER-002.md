# NFR-USER-002.md - 비밀번호 입력 보안 명세서

## 1. API 및 기능 개요

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | `NFR-USER-002` |
| 분류 | 비기능 요구사항 (Non-Functional Requirement) |
| 기능 명 | 비밀번호 입력 보안 (Password Input Security) |
| 설명 | 모든 비밀번호 입력 시 마스킹 처리를 진행하며, 아이콘 클릭을 통해 입력한 비밀번호를 확인할 수 있도록 한다. |
| 적용 범위 | 회원가입 (`01_signup.md`), 로그인 (`02_auth.md`), 비밀번호 변경 (`03_mypage.md`) 등 모든 비밀번호 입력 필드 |

---

## 2. 요청 및 UI 규칙 (Request & UI Rules)

### 2.1 마스킹 (Masking) 처리 규칙

- 비밀번호 입력 필드의 HTML `type` 속성은 기본적으로 `password`를 사용한다.
- 입력된 문자는 화면상에 불투명한 마스킹 기호(`*` 또는 `●`)로 표시하여 외부에 노출되지 않도록 한다.
- 브라우저 자동완성 기능 구분을 위해 용도에 맞춰 속성을 지정한다:
  - 회원가입 / 새 비밀번호: `autocomplete="new-password"`
  - 로그인 / 현재 비밀번호: `autocomplete="current-password"`

### 2.2 가시성 토글 (Visibility Toggle) 규칙

- 비밀번호 입력 필드 우측 내부에 토글 전용 버튼 아이콘을 위치시킨다.
- 토글 버튼 클릭 시 Input의 `type` 속성을 `password` $\leftrightarrow$ `text`로 실시간 전환한다.
- 토글 버튼에는 반드시 `type="button"` 속성을 부여하여 클릭 시 폼(Form)이 제출되는 현상을 방지한다.
- 토글 상태 변화에 따라 웹 접근성 속성(`aria-label`, `aria-pressed`) 및 아이콘 모습을 변경한다.

---

## 3. 명세 필드 및 상태표

### 토글 상태별 명세

| 토글 상태 | Input Type | 표시 아이콘 | aria-label (접근성 라벨) | aria-pressed |
| --- | --- | --- | --- | --- |
| **기본 (마스킹)** | `password` | Eye Icon (눈 모양) | `비밀번호 표시` | `false` |
| **활성 (보기)** | `text` | Eye Off Icon (사선 눈) | `비밀번호 숨기기` | `true` |

---

## 4. 프론트엔드 예시 (Client Implementation Example)

```html
<div class="password-field">
  <label for="password">비밀번호</label>
  <div class="input-container">
    <input 
      type="password" 
      id="password" 
      name="password" 
      autocomplete="current-password" 
      placeholder="비밀번호를 입력해 주세요" 
      required
    />
    <button 
      type="button" 
      id="togglePasswordBtn" 
      class="toggle-btn" 
      aria-label="비밀번호 표시" 
      aria-pressed="false"
    >
      <span class="icon">👁️</span>
    </button>
  </div>
</div>

<script>
  const passwordInput = document.getElementById('password');
  const toggleBtn = document.getElementById('togglePasswordBtn');

  toggleBtn.addEventListener('click', () => {
    const isPassword = passwordInput.getAttribute('type') === 'password';
    
    // Type 전환 (password <-> text)
    passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
    
    // 웹 접근성 및 아이콘 상태 변경
    toggleBtn.setAttribute('aria-pressed', isPassword ? 'true' : 'false');
    toggleBtn.setAttribute('aria-label', isPassword ? '비밀번호 숨기기' : '비밀번호 표시');
    toggleBtn.querySelector('.icon').textContent = isPassword ? '🙈' : '👁️';
  });
</script>
```

---

## 5. 비고 및 보안 지침 (Security Notes)

- **평문 노출 제어**: 가시성 토글은 UI 상에서의 표시 전환 기능일 뿐이며, 콘솔 출력(`console.log`)이나 클라이언트 스토리지(LocalStorage / SessionStorage)에 평문 비밀번호를 절대 남기지 않는다.
- **네트워크 보안**: 비밀번호 가시성 상태와 무관하게, 서버로 전송되는 모든 비밀번호 데이터는 HTTPS (TLS) 통신을 통해 안전하게 암호화되어 전송된다.
- **공통 규칙 준수**: 본 비기능 요구사항은 프로젝트 내 모든 비밀번호 입력 관련 API 및 프론트엔드 화면에 일관되게 적용한다.
