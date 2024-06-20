const socket = io('http://localhost:5000');

const app = new Vue({
    el: '#app',
    data: {
        classroomName: '',
        classroomCode: '',
        joinCode: '',
        userName: '',
        inClassroom: false,
        joinedClassName: '',
        joinedClassCode: '',
        files: [],
        messages: [],
        newMessage: '',
        classes: [],
        socketConnected: false,
        rating: 0,
        averageRating: 0,
        ratingCount: 0,
        onlineUsers: []  // 新增
    },
    methods: {
        async createClassroom() {
            console.log("Creating classroom...");
            try {
                const response = await axios.post('http://localhost:5000/create_class', { classroomName: this.classroomName });
                console.log(response.data);
                this.classroomCode = response.data.classroomCode;
                this.fetchClasses();
            } catch (error) {
                console.error('Error creating classroom:', error);
            }
        },
        async joinClassroom() {
            console.log("Joining classroom...");
            try {
                const response = await axios.post('http://localhost:5000/join_class', { joinCode: this.joinCode, userName: this.userName });
                console.log(response.data);
                if (response.data.success) {
                    this.inClassroom = true;
                    const classroom = this.classes.find(classroom => classroom.code === this.joinCode);
                    this.joinedClassName = classroom.name;
                    this.joinedClassCode = this.joinCode;
                    this.averageRating = classroom.average_rating;
                    this.ratingCount = classroom.rating_count;
                    if (!this.socketConnected) {
                        socket.on('receive_message', (message) => {
                            if (!this.messages.some(m => m.id === message.id)) {
                                this.messages.push(message);
                            }
                        });
                        socket.on('user_list', (users) => {
                            this.onlineUsers = users;
                        });
                        this.socketConnected = true;
                    }
                    socket.emit('join', { user_name: this.userName, class_code: this.joinCode });
                } else {
                    alert('Invalid classroom code');
                }
            } catch (error) {
                console.error('Error joining classroom:', error);
            }
        },
        async submitRating() {
            try {
                const response = await axios.post('http://localhost:5000/rate_class', { classCode: this.joinedClassCode, rating: this.rating });
                if (response.data.success) {
                    alert('評分提交成功');
                    this.fetchClasses();
                } else {
                    alert('提交評分失敗');
                }
            } catch (error) {
                console.error('Error submitting rating:', error);
            }
        },
        async deleteClass(classCode) {
            console.log("Deleting class...");
            try {
                const response = await axios.post('http://localhost:5000/delete_class', { classCode: classCode });
                console.log(response.data);
                this.fetchClasses();
            } catch (error) {
                console.error('Error deleting class:', error);
            }
        },
        async uploadFile(event) {
            console.log("Uploading file...");
            const file = event.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);
                try {
                    const response = await axios.post('http://localhost:5000/upload', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    });
                    console.log(response.data);
                    this.files.push({ name: response.data.name, url: response.data.url });
                } catch (error) {
                    console.error('Error uploading file:', error);
                }
            }
        },
        sendMessage() {
            console.log("Sending message...");
            if (this.newMessage.trim()) {
                const message = { user: this.userName, text: this.newMessage, id: uuidv4(), class_code: this.joinedClassCode };
                socket.emit('send_message', message);  // 通過 Socket.io 發送消息
                this.newMessage = '';
            }
        },
        async fetchClasses() {
            console.log("Fetching classes...");
            try {
                const response = await axios.get('http://localhost:5000/get_classes');
                this.classes = response.data;
            } catch (error) {
                console.error('Error fetching classes:', error);
            }
        }
    },
    mounted() {
        this.fetchClasses(); 
    }
});

// UUID generation function
function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
