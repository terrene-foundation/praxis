// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Firebase Authentication configuration for the Praxis web dashboard.
 *
 * Firebase handles SSO login (GitHub, Google) on the frontend.
 * After sign-in, the Firebase ID token is sent to the Praxis backend
 * which verifies it and returns a Praxis JWT.
 *
 * The Firebase API key is safe to expose in frontend code -- it is
 * designed to be public and scoped to the Firebase project.
 */

import { initializeApp } from "firebase/app";
import { getAuth, GithubAuthProvider, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "",
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const githubProvider = new GithubAuthProvider();
export const googleProvider = new GoogleAuthProvider();
