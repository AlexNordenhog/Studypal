import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { GoogleAuthProvider, getAuth, signInWithPopup, onAuthStateChanged, updateProfile } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { getDatabase, ref, get, child, set } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-database.js";
import firebaseConfig from "./firebase-cfg.js";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
const db = getDatabase();


function userExists(uid) {

    const dbRef = ref(getDatabase());
    
    get(child(dbRef, "Users/")).then((snapshot) => {
        let userExists = false;
        snapshot.forEach((childSnapshot) => {
            const current_uid = childSnapshot.key;
            if (uid === current_uid) {
                userExists = true;
                return true;
            }
        });
    }).catch((error) => {
        console.error(error);
    });

    return false
}



onAuthStateChanged(auth, (user) => {
if (user) {
    // User is signed in, see docs for a list of available properties
    // https://firebase.google.com/docs/reference/js/auth.user
    
    const uid = user.uid;
    
    if (userExists(uid)) {
        // move on as usual
    }
    else {
        // create new user, ask for username
    }
    
    

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

