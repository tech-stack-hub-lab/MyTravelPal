document.addEventListener("DOMContentLoaded", () => {

    const buttons = document.querySelectorAll(".btn-primary");

    buttons.forEach(btn => {

        btn.addEventListener("mouseenter", () => {
            btn.style.transform = "translateY(-2px)";
            btn.style.transition = "0.3s";
        });

        btn.addEventListener("mouseleave", () => {
            btn.style.transform = "translateY(0)";
        });

    });

});




// /* LOGIN BUTTON */

// document.getElementById("loginBtn").addEventListener("click", () => {

//     // Redirect to login page
//     window.location.href = "login.html";

// });


// /* GET STARTED BUTTON */

// document.getElementById("startBtn").addEventListener("click", () => {

//     // Redirect to signup page
//     window.location.href = "signup.html";

// });


/* SCROLL ANIMATION */

const cards1 = document.querySelectorAll(".feature-card");

cards1.forEach(card1 => {
    card1.classList.add("hidden");
});

const observer = new IntersectionObserver((entries)=>{

    entries.forEach(entry=>{

        if(entry.isIntersecting){

            entry.target.classList.remove("hidden");
            entry.target.classList.add("show");
        }

    });

},{
    threshold:0.15
});

cards1.forEach(card1=>{
    observer.observe(card1);
});




const destinationData = {

    europe: [

        {
            city: "Paris",
            country: "France",
            tag: "Romance",
            image:
              "https://images.unsplash.com/photo-1431274172761-fca41d930114?w=800"
        },

        {
            city: "Santorini",
            country: "Greece",
            tag: "Beach",
            image:
              "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800"
        },

        {
            city: "Rome",
            country: "Italy",
            tag: "History",
            image:
              "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800"
        }

    ],

    asia: [

        {
            city: "Tokyo",
            country: "Japan",
            tag: "Modern",
            image:
              "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800"
        },

        {
            city: "Bali",
            country: "Indonesia",
            tag: "Island",
            image:
              "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800"
        },

        {
            city: "Bangkok",
            country: "Thailand",
            tag: "Culture",
            image:
              "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=800"
        }

    ],

    americas: [

        {
            city: "New York",
            country: "USA",
            tag: "City",
            image:
              "https://images.unsplash.com/photo-1499092346589-b9b6be3e94b2?w=800"
        },

        {
            city: "Rio",
            country: "Brazil",
            tag: "Beach",
            image:
              "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800"
        },

        {
            city: "Toronto",
            country: "Canada",
            tag: "Urban",
            image:
              "https://images.unsplash.com/photo-1517935706615-2717063c2225?w=800"
        }

    ],

    africa: [

        {
            city: "Cape Town",
            country: "South Africa",
            tag: "Nature",
            image:
              "https://images.unsplash.com/photo-1576485290814-1c72aa4bbb8e?w=800"
        },

        {
            city: "Marrakech",
            country: "Morocco",
            tag: "Culture",
            image:
              "https://images.unsplash.com/photo-1597212618440-806262de4f6b?w=800"
        },

        {
            city: "Cairo",
            country: "Egypt",
            tag: "History",
            image:
              "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=800"
        }

    ],

    middleeast: [

        {
            city: "Dubai",
            country: "UAE",
            tag: "Luxury",
            image:
              "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800"
        },

        {
            city: "Doha",
            country: "Qatar",
            tag: "Modern",
            image:
              "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=800"
        },

        {
            city: "Muscat",
            country: "Oman",
            tag: "Adventure",
            image:
              "https://images.unsplash.com/photo-1564459532916-ff84c46f9ed8?w=800"
        }

    ]
};

const grid = document.getElementById("destinationGrid");
const tabs = document.querySelectorAll(".tab");

function loadDestinations(category){

    grid.innerHTML = "";

    destinationData[category].forEach(item => {

        grid.innerHTML += `
            <div class="destination-card">

                <img src="${item.image}" alt="${item.city}">

                <div class="overlay">
                    <span class="tag-label">${item.tag}</span>
                    <h3 class="city">${item.city}</h3>
                    <p class="country">${item.country}</p>
                </div>

            </div>
        `;

    });

}

loadDestinations("europe");

tabs.forEach(tab => {

    tab.addEventListener("click", () => {

        tabs.forEach(btn =>
            btn.classList.remove("active")
        );

        tab.classList.add("active");

        const category =
            tab.dataset.category;

        loadDestinations(category);

    });

});

// ======================================
// Card Glow Effect
// ======================================

const statcards = document.querySelectorAll(
    ".stat-card,.step-card,.pricing-card"
);

statcards.forEach((statcard) => {

    statcard.addEventListener("mousemove", (e) => {

        const rect = statcard.getBoundingClientRect();

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        statcard.style.background =
            `radial-gradient(circle at ${x}px ${y}px,
            rgba(214,171,82,.12),
            rgba(255,255,255,.03) 60%)`;

    });

    statcard.addEventListener("mouseleave", () => {

        statcard.style.background =
            "rgba(255,255,255,.03)";
    });
});


// ======================================
// CTA Button
// ======================================

const ctaButton = document.querySelector(".cta-btn");

if(ctaButton){

    ctaButton.addEventListener("click", () => {

        alert("Create Account functionality goes here.");

    });
}

/* ========================================
   ASSISTANT BUTTON
======================================== */

/* ========================================
   CHAT WIDGET
======================================== */

const assistantBtn =
document.querySelector(".assistant-btn");

const chatPopup =
document.querySelector(".chat-popup");

const closeChat =
document.querySelector(".close-chat");

const sendBtn =
document.querySelector("#sendBtn");

const chatInput =
document.querySelector("#chatInput");

const chatBody =
document.querySelector(".chat-body");

/* Open Chat */

assistantBtn.addEventListener("click", () => {

    chatPopup.classList.toggle("active");

});

/* Close Chat */

closeChat.addEventListener("click", () => {

    chatPopup.classList.remove("active");

});

/* Send Message */

function sendMessage(){

    const message = chatInput.value.trim();

    if(message === "") return;

    // User Message

    const userMessage =
    document.createElement("div");

    userMessage.className = "user-message";

    userMessage.innerText = message;

    chatBody.appendChild(userMessage);

    chatInput.value = "";

    // Send to backend chat API
    (async () => {
        try {
            const csrftoken = (document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/)||[])[2];
            const res = await fetch('/chat/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken || ''
                },
                body: JSON.stringify({message})
            });
            const data = await res.json();
            const botReply = document.createElement('div');
            botReply.className = 'bot-message';
            botReply.innerHTML = data.reply || data.error || 'No response';
            chatBody.appendChild(botReply);
            chatBody.scrollTop = chatBody.scrollHeight;
        } catch (err) {
            const botReply = document.createElement('div');
            botReply.className = 'bot-message';
            botReply.innerText = 'Chat service unavailable.';
            chatBody.appendChild(botReply);
        }
    })();

    chatBody.scrollTop =
    chatBody.scrollHeight;
}

/* Button Click */

sendBtn.addEventListener(
    "click",
    sendMessage
);

/* Enter Key */

chatInput.addEventListener("keypress", (e)=>{

    if(e.key === "Enter"){

        sendMessage();

    }

});

/* ========================================
   FOOTER LINK ANIMATION
======================================== */

const footerLinks = document.querySelectorAll('.footer-links a');

footerLinks.forEach(link => {

    link.addEventListener('mouseenter', () => {
        link.style.transform = 'translateY(-2px)';
    });

    link.addEventListener('mouseleave', () => {
        link.style.transform = 'translateY(0)';
    });

});



// Animated stats cards

const animatedcards = document.querySelectorAll(".stat-card");

animatedcards.forEach(animatedcard => {

    animatedcard.addEventListener("mousemove", (e) => {

        const rect = animatedcard.getBoundingClientRect();

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        animatedcard.style.transform =
        `perspective(1000px)
        rotateX(${-(y - rect.height/2)/20}deg)
        rotateY(${(x - rect.width/2)/20}deg)
        translateY(-5px)`;

    });

    animatedcard.addEventListener("mouseleave", () => {
        animatedcard.style.transform = "translateY(0)";
    });

});

// Notification pulse

const badge = document.querySelector(".notification span");

setInterval(() => {
    badge.classList.toggle("pulse");
},1000);