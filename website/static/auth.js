import {
    initializeApp
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";

import {
    GoogleAuthProvider,
    getAuth,
    signInWithPopup,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";

import {
    getDatabase,
    ref,
    get,
    child,
    set
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-database.js";

import firebaseConfig from "./firebase-cfg.js";

// Initialize firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// Check if user has created a profile
function userExists(uid) {
    const dbRef = ref(getDatabase());

    get(child(dbRef, "Users/"))
        .then((snapshot) => {
            let userExists = false;
            snapshot.forEach((childSnapshot) => {
                const current_uid = childSnapshot.key;
                if (uid === current_uid) {
                    userExists = true;
                    return true;
                }
            });
        })
        .catch((error) => {
            console.error(error);
        });

    return false;
}

export { app, auth, provider, userExists };