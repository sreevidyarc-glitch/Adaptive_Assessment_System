# Integrated Algorithm: Authentication- and Privacy-Aware Adaptive Assessment System

## 1. Purpose

This algorithm describes an adaptive assessment workflow that maps
course content to learning objectives, generates and validates
questions, evaluates student responses, identifies learning gaps, and
recommends remedial learning. Authentication and authorization checks
are applied at each protected stage.

## 2. Inputs

  Symbol   Description
  -------- ---------------------------------------------
  `C`      Course material
  `O`      Set of course learning objectives
  `T`      Set of assessment traits
  `W`      Weights associated with assessment evidence
  `Q`      Question allocation information
  `N`      Total number of questions
  `τ`      Target mastery threshold
  `S`      Module-wise paragraph/sentence chunks
  `M`      Objective--trait mastery matrix
  `G`      Objective--trait learning-gap scores

## 3. Integrated pseudocode

``` text
BEGIN

  [AUTH] Faculty LOGIN (email, password) + OTP

         IF authentication failed OR role != "FACULTY" THEN
             RAISE AccessDenied
         END IF

         Issue faculty session token (expires in 30 minutes)

  INPUT C, O, T, W, Q, N, τ

  [AUTH] Verify that the authenticated faculty member
         is assigned to the specified course.

         IF faculty is not assigned to the course THEN
             RAISE UnauthorizedCourseAccess
         END IF

  1. Split course material into module-wise
     paragraph/sentence chunks S.

  2. FOR each chunk sᵢ:

         Compute cosine similarity with each objective oⱼ.
         Assign sᵢ to the most similar objective.

     END FOR

     Report objectives with no matching chunks
     as coverage gaps.

  3. Allocate N questions across objectives
     using the largest remainder method.

     Allocate questions across traits
     using remaining quota deficits.

  4. FOR each allocated question:

         Retrieve relevant chunks.

         [AUTH] Call the LLM service using a secret API key
                stored securely on the server.

         Generate:
             Question
             Rubric
             Model answer
             Hint 1
             Hint 2

         Validate:
             Schema
             Hint leakage
             Rubric sanity
             Duplicate questions

         Retry up to 3 times.

         IF validation still fails THEN
             Send unresolved failures to authorized faculty.
         END IF

     END FOR

     [AUTH] Faculty approves the generated question set.

     [AUTH] Rubrics and model answers are visible
            to authorized faculty only and are never
            exposed to students.

  [AUTH] Student LOGIN (roll number + password
         OR institutional SSO)

         Verify student identity and enrollment
         in the specified course.

         IF student is not enrolled THEN
             RAISE UnauthorizedAssessmentAccess
         END IF

         Issue student session token (expires in 60 minutes)

  5. Evaluate student responses using the approved rubrics.

     FOR each objective–trait pair (o, t):

         Calculate:

         fᵢ = earned rubric points / total rubric points

         Mₒ,ₜ = (1 + Σ wᵢ fᵢ) / (2 + Σ wᵢ)

         Store each Mₒ,ₜ separately in mastery matrix M.

     END FOR

     [AUTH] Student can view only their own mastery matrix M.
            Authorized faculty can view the class-level
            mastery matrix, subject to institutional permissions.

  6. FOR each objective–trait pair (o, t):

         Calculate:

         Gₒ,ₜ = (τ − Mₒ,ₜ) × wₒ

     END FOR

     Rank learning gaps in descending order.

     IF Mₒ,ₜ < 0.3 THEN
         Recommend foundational learning.
     ELSE
         Recommend reinforcement learning.
     END IF

     Generate personalized remedial learning packs.

     [AUTH] Deliver each remedial pack only to the
            corresponding authenticated student.

  7. [AUTH] Re-verify the student's session token
            before starting the post-assessment.

     IF token is expired OR invalid THEN
         Require student to authenticate again.
     END IF

     Conduct post-assessment with progressive hints.

     IF Pre = 1 THEN
         RAISE exception:
         "Normalized gain is undefined when Pre = 1."
     ELSE
         Calculate:

         g = (Post − Pre) / (1 − Pre)
     END IF

  [AUTH] Report access:

         Student  → Can view own assessment report only.
         Faculty  → Can view authorized class-level reports.

  [AUTH] LOGOUT and invalidate the active session token.

  RETURN:
      Validated questions,
      Mastery matrix,
      Remedial learning packs,
      Assessment report,
      Normalized learning gain.

END
```

## 4. Authentication and authorization requirements

  -----------------------------------------------------------------------
  Workflow stage                      Required control
  ----------------------------------- -----------------------------------
  Faculty login                       Email/password and OTP; verify
                                      faculty role

  Course processing                   Confirm faculty-course assignment

  LLM invocation                      Keep API key in server-side secret
                                      storage; never expose it in client
                                      code

  Question approval                   Require authenticated faculty
                                      authorization

  Question publication                Students receive questions only;
                                      rubrics and model answers remain
                                      faculty-only

  Student login                       Institutional SSO or roll-number
                                      credentials

  Assessment access                   Verify course enrollment

  Mastery results                     Students access only their own
                                      results; faculty access is limited
                                      to authorized classes

  Remedial learning                   Deliver packs to the corresponding
                                      authenticated student

  Post-assessment                     Re-verify session validity

  Reports                             Enforce student-level and
                                      faculty-level access restrictions

  Logout                              Revoke/invalidate the session token
  -----------------------------------------------------------------------

## 5. Privacy and security requirements

The implementation should apply the following safeguards:

1.  **Credential protection:** Store passwords using a strong, salted
    password-hashing algorithm. Never store plaintext passwords.
2.  **OTP security:** Use short-lived, single-use OTPs with attempt
    limits and resend controls.
3.  **Session security:** Use securely generated, short-lived tokens.
    Validate token expiry, signature, issuer, audience, and revocation
    status. Prefer secure, HttpOnly, SameSite cookies for browser
    sessions.
4.  **API-key protection:** Store the LLM API key in server-side
    environment secrets or a secrets manager. Do not hard-code it,
    commit it to GitHub, or send it to the browser.
5.  **Data encryption:** Use HTTPS/TLS for data in transit and
    encryption at rest for sensitive stored data.
6.  **Student privacy:** Use pseudonymous student identifiers in
    analytics and avoid sending names, roll numbers, or other direct
    identifiers to the LLM service.
7.  **Least-privilege access:** Enforce authorization on the backend for
    every protected request; hiding a user-interface element is not an
    access-control mechanism.
8.  **Audit logging:** Record relevant login, access, approval,
    assessment, report, and administrative events without logging
    passwords, OTPs, session tokens, or API keys.
9.  **Data retention:** Define retention periods and secure deletion
    procedures for student responses, scores, and account data.
10. **External AI processing:** Review the LLM provider's
    data-processing, retention, and training settings before sending
    course or assessment content.

## 6. Implementation notes and validation checks

-   Treat the 30-minute faculty token and 60-minute student token as
    maximum session lifetimes. Invalidate tokens on logout and when
    relevant account or session security events occur.
-   A session token should be validated by the backend on every
    protected API request. Re-verification before post-assessment is an
    additional checkpoint, not a substitute for per-request validation.
-   The LLM API key is a server-to-server credential. The `[AUTH]` label
    indicates secure service authorization; it does not mean a faculty
    member should provide the key.
-   Ensure that the rubric denominator is greater than zero before
    calculating `fᵢ`.
-   Ensure all evidence weights `wᵢ` are non-negative and that the
    denominator in the mastery equation is positive.
-   Define how ties are handled when assigning a chunk to equally
    similar objectives.
-   Define whether `wₒ` in the gap equation is an objective-priority
    weight and normalize or document its scale.
-   Confirm that `Pre` and `Post` are normalized to the interval
    `[0, 1]` before calculating normalized gain. The `Pre = 1` case is
    undefined; also validate input ranges.
-   Specify how missing responses, unattempted questions, and partial
    rubric evidence are handled.
-   Keep the model answer and rubric in protected server-side storage
    and exclude them from student-facing API responses.

## 7. Suggested project structure for Antigravity

``` text
adaptive-assessment-system/
├── README.md
├── docs/
│   ├── integrated_algorithm.md
│   ├── authentication_and_authorization.md
│   └── privacy_and_security.md
├── backend/
│   ├── auth/
│   ├── course_mapping/
│   ├── question_generation/
│   ├── assessment/
│   ├── mastery_analytics/
│   └── remedial_learning/
├── frontend/
│   ├── faculty/
│   └── student/
├── tests/
│   ├── authentication/
│   ├── authorization/
│   ├── privacy/
│   └── assessment/
└── .env.example
```


