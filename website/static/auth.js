import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { GoogleAuthProvider, getAuth, signInWithPopup, onAuthStateChanged, updateProfile } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { getDatabase, ref, get, child, set } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-database.js";

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

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
const db = getDatabase();

onAuthStateChanged(auth, (user) => {
if (user) {
    // User is signed in, see docs for a list of available properties
    // https://firebase.google.com/docs/reference/js/auth.user
    
    const uid = user.uid;

    //uname = get(ref(database), 'Users/' + uid)
    //alert(uname)


    window.location.href = '/profile'
    // ...
} else {
    
    document.getElementById("login_text").textContent = "Login Options"
    // User is signed out
    // ...
}
});

document.getElementById("google_login_btn").addEventListener("click", function(){
signInWithPopup(auth, provider)
    .then((result) => {
    // This gives you a Google Access Token. You can use it to access the Google API.
    const credential = GoogleAuthProvider.credentialFromResult(result);
    const token = credential.accessToken;
    // The signed-in user info.
    const user = result.user;
    
    //window.location.href = "/profile"

    }).catch((error) => {
    // Handle Errors here.
    const errorCode = error.code;
    const errorMessage = error.message;
    // The email of the user's account used.
    const email = error.customData.email;
    // The AuthCredential type that was used.
    const credential = GoogleAuthProvider.credentialFromError(error);
    });
});

