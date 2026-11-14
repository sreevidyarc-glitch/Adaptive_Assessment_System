import client from './client';

export const authApi = {
  facultyLoginInit: async (email, password) => {
    const res = await client.post('/auth/faculty/login-init', { email, password });
    return res.data;
  },

  facultyVerifyOTP: async (session_ticket, otp_code) => {
    const res = await client.post('/auth/faculty/verify-otp', { session_ticket, otp_code });
    return res.data;
  },

  studentLogin: async (identifier, password) => {
    const res = await client.post('/auth/student/login', { identifier, password });
    return res.data;
  },

  logout: async () => {
    try {
      await client.post('/auth/logout');
    } catch (e) {
      console.warn('Logout API error:', e);
    } finally {
      localStorage.removeItem('adaptive_token');
      localStorage.removeItem('adaptive_user');
      localStorage.removeItem('adaptive_role');
    }
  },

  getMe: async () => {
    const res = await client.get('/auth/me');
    return res.data;
  },

  getFacultyDashboard: async () => {
    const res = await client.get('/faculty/dashboard');
    return res.data;
  },

  approveQuestion: async (questionId, isApproved, isPublished = false) => {
    const res = await client.patch(`/faculty/questions/${questionId}/approve`, {
      is_approved: isApproved,
      is_published: isPublished,
    });
    return res.data;
  },

  uploadCourseMaterial: async (courseId, file, threshold = 0.35) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('similarity_threshold', threshold);

    const res = await client.post(`/faculty/courses/${courseId}/materials/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  getCourseMaterialMapping: async (courseId, threshold = 0.35) => {
    const res = await client.get(`/faculty/courses/${courseId}/materials/mapping`, {
      params: { similarity_threshold: threshold },
    });
    return res.data;
  },

  generateQuestions: async (courseId, totalQuestions = 5) => {
    const res = await client.post(`/faculty/courses/${courseId}/questions/generate`, {
      total_questions: totalQuestions,
    });
    return res.data;
  },

  getCourseQuestionsForFaculty: async (courseId) => {
    const res = await client.get(`/faculty/courses/${courseId}/questions`);
    return res.data;
  },

  batchApproveQuestions: async (courseId, questionIds, isApproved = true, isPublished = true) => {
    const res = await client.post(`/faculty/courses/${courseId}/questions/batch-approve`, {
      question_ids: questionIds,
      is_approved: isApproved,
      is_published: isPublished,
    });
    return res.data;
  },

  getStudentDashboard: async () => {
    const res = await client.get('/student/dashboard');
    return res.data;
  },

  getStudentCourseQuestions: async (courseId) => {
    const res = await client.get(`/student/courses/${courseId}/questions`);
    return res.data;
  },

  startAssessmentSession: async (courseId) => {
    const res = await client.post(`/student/courses/${courseId}/assessments/start`);
    return res.data;
  },

  submitAssessmentSession: async (sessionId, responses) => {
    const res = await client.post(`/student/assessments/${sessionId}/submit`, { responses });
    return res.data;
  },

  getStudentMasteryMatrix: async (courseId) => {
    const res = await client.get(`/student/courses/${courseId}/mastery-matrix`);
    return res.data;
  },

  getClassMasteryMatrix: async (courseId, tau = 0.75) => {
    const res = await client.get(`/faculty/courses/${courseId}/mastery-matrix`, {
      params: { tau },
    });
    return res.data;
  },

  getRemedialPacks: async (courseId) => {
    const res = await client.get(`/student/courses/${courseId}/remedial-packs`);
    return res.data;
  },

  completeRemedialPack: async (packId) => {
    const res = await client.patch(`/student/remedial-packs/${packId}/complete`);
    return res.data;
  },

  startPostAssessment: async (courseId) => {
    const res = await client.post(`/student/courses/${courseId}/post-assessments/start`);
    return res.data;
  },

  submitPostAssessment: async (sessionId, responses) => {
    const res = await client.post(`/student/post-assessments/${sessionId}/submit`, { responses });
    return res.data;
  },

  getStudentAssessmentReport: async (courseId) => {
    const res = await client.get(`/student/courses/${courseId}/assessment-report`);
    return res.data;
  },

  getFacultyAssessmentReport: async (courseId, tau = 0.75) => {
    const res = await client.get(`/faculty/courses/${courseId}/assessment-report`, {
      params: { tau },
    });
    return res.data;
  },
};



