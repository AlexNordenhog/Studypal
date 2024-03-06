import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { GoogleAuthProvider, getAuth, signInWithPopup, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { getDatabase, ref, set, get, child } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-database.js";

const firebaseConfig = {
    apiKey: "AIzaSyAjihd9ILzcVlPzCWrr4SLVJCOw6I1nzAc",
    authDomain: "studypal-8a379.firebaseapp.com",
    databaseURL: "https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "studypal-8a379",
    storageBucket: "studypal-8a379.appspot.com",
    messagingSenderId: "475383216328",
    appId: "1:475383216328:web:dcebc7bfd95236ebd7cdfd",
    measurementId: "G-68F0PLPVS6"
    };

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();