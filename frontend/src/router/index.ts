import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      redirect: '/interviews',
      children: [
        { path: 'interviews', name: 'Interviews', component: () => import('@/views/InterviewsView.vue') },
        { path: 'resumes', name: 'Resumes', component: () => import('@/views/ResumesView.vue') },
        { path: 'share', name: 'Share', component: () => import('@/views/ShareView.vue') },
        { path: 'profile', name: 'Profile', component: () => import('@/views/ProfileView.vue') },
        { path: 'messages', name: 'Messages', component: () => import('@/views/MessagesView.vue') },
        { path: 'settings', redirect: '/profile' },
      ],
    },
  ],
})

export default router
