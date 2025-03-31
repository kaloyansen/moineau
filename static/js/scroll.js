const { createApp } = Vue;

createApp({
    data() {
        return {
            text: "loading..."
        };
    },
    mounted() {
        this.fetchText();
        setInterval(this.fetchText, 1e4); // fetch new text every 10 seconds
    },
    methods: {
        async fetchText() {
            try {
                const response = await fetch('/src'); // flask API url
                const data = await response.json();
                this.text = data.text;
            } catch (error) {
                console.error("error fetching text:", error);
            }
        }
    }
}).mount("#app");
