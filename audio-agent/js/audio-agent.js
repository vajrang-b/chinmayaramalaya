/**
 * CHINMAYA RAMALAYA - AUDIO AI AGENT CORE ENGINE
 * Real-time Speech Recognition, Devotional Knowledge QA & Speech Synthesis
 */

class RamalayaAudioAgent {
    constructor() {
        this.knowledgeBase = null;
        this.recognition = null;
        this.synth = window.speechSynthesis;
        this.isListening = false;
        this.isSpeaking = false;
        this.animFrameId = null;
        this.voices = [];
        
        // DOM Elements
        this.micBtn = document.getElementById('micBtn');
        this.statusText = document.getElementById('statusText');
        this.statusDot = document.getElementById('statusDot');
        this.userQueryEl = document.getElementById('userQuery');
        this.agentResponseEl = document.getElementById('agentResponse');
        this.textInput = document.getElementById('textInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.voiceSelect = document.getElementById('voiceSelect');
        this.canvas = document.getElementById('visualizerCanvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;

        this.init();
    }

    async init() {
        await this.loadKnowledgeBase();
        this.setupSpeechRecognition();
        this.setupVoices();
        this.setupEventListeners();
        this.initVisualizer();
    }

    async loadKnowledgeBase() {
        try {
            const response = await fetch('data/knowledge.json');
            this.knowledgeBase = await response.json();
            console.log('✅ Audio Agent Knowledge Base Loaded:', this.knowledgeBase);
        } catch (err) {
            console.error('❌ Failed to load knowledge base:', err);
        }
    }

    setupVoices() {
        if (!this.synth) return;

        const populate = () => {
            this.voices = this.synth.getVoices();
            if (!this.voiceSelect || this.voices.length === 0) return;

            this.voiceSelect.innerHTML = '';
            
            // Sort & filter English voices, prioritizing Google / Natural / Apple / Microsoft voices
            const sortedVoices = [...this.voices].sort((a, b) => {
                const aQuality = (a.name.includes('Google') || a.name.includes('Natural') || a.name.includes('Premium')) ? 2 : 1;
                const bQuality = (b.name.includes('Google') || b.name.includes('Natural') || b.name.includes('Premium')) ? 2 : 1;
                return bQuality - aQuality;
            });

            let defaultIdx = 0;
            sortedVoices.forEach((voice, index) => {
                if (voice.lang.startsWith('en')) {
                    const option = document.createElement('option');
                    option.value = voice.name;
                    option.textContent = `${voice.name} (${voice.lang})`;
                    
                    // Auto-select best voice
                    if (voice.name.includes('Google US English') || voice.name.includes('Google UK English') || voice.name.includes('Natural') || voice.lang === 'en-IN') {
                        defaultIdx = index;
                    }
                    this.voiceSelect.appendChild(option);
                }
            });

            if (this.voiceSelect.options.length > 0) {
                this.voiceSelect.selectedIndex = defaultIdx;
            }
        };

        populate();
        if (typeof this.synth.onvoiceschanged !== 'undefined') {
            this.synth.onvoiceschanged = populate;
        }
    }

    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('⚠️ Web Speech API not supported in this browser. Falling back to text mode.');
            if (this.statusText) {
                this.statusText.textContent = 'Voice input not supported in this browser. Use text input below.';
            }
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateStatus('Listening for your voice...', true);
            if (this.micBtn) this.micBtn.classList.add('listening');
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const currentText = finalTranscript || interimTranscript;
            if (this.userQueryEl) {
                this.userQueryEl.textContent = `"${currentText}"`;
            }

            if (finalTranscript) {
                this.processQuery(finalTranscript);
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech Recognition Error:', event.error);
            this.stopListening();
            this.updateStatus('Could not understand audio. Please try again or type below.', false);
        };

        this.recognition.onend = () => {
            this.stopListening();
        };
    }

    setupEventListeners() {
        if (this.micBtn) {
            this.micBtn.addEventListener('click', () => this.toggleListening());
        }

        if (this.sendBtn && this.textInput) {
            this.sendBtn.addEventListener('click', () => {
                const text = this.textInput.value.trim();
                if (text) {
                    this.userQueryEl.textContent = `"${text}"`;
                    this.processQuery(text);
                    this.textInput.value = '';
                }
            });

            this.textInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendBtn.click();
                }
            });
        }

        // Handle Chip buttons
        document.querySelectorAll('.chip-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.target.getAttribute('data-query');
                if (query) {
                    if (this.userQueryEl) this.userQueryEl.textContent = `"${query}"`;
                    this.processQuery(query);
                }
            });
        });

        // Handle Sloka Listen buttons
        document.querySelectorAll('.btn-listen-sloka').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const text = e.target.getAttribute('data-sloka');
                if (text) {
                    this.speakResponse(text);
                }
            });
        });
    }

    toggleListening() {
        if (!this.recognition) {
            alert('Speech Recognition is not supported on your browser. Please type your question in the text box.');
            return;
        }

        if (this.isListening) {
            this.stopListening();
        } else {
            if (this.synth && this.synth.speaking) {
                this.synth.cancel();
            }
            try {
                this.recognition.start();
            } catch (e) {
                console.error('Recognition start error:', e);
            }
        }
    }

    stopListening() {
        this.isListening = false;
        if (this.micBtn) this.micBtn.classList.remove('listening');
        if (this.statusDot) this.statusDot.classList.remove('active');
        if (!this.isSpeaking) {
            this.updateStatus('Tap microphone to speak or type a question below.', false);
        }
    }

    updateStatus(message, isActive) {
        if (this.statusText) this.statusText.textContent = message;
        if (this.statusDot) {
            if (isActive) this.statusDot.classList.add('active');
            else this.statusDot.classList.remove('active');
        }
    }

    processQuery(rawQuery) {
        if (!this.knowledgeBase) return;

        const query = rawQuery.toLowerCase();
        let bestMatch = null;
        let maxScore = 0;

        for (const item of this.knowledgeBase.qa_pairs) {
            let score = 0;
            for (const kw of item.keywords) {
                if (query.includes(kw.toLowerCase())) {
                    score += 1;
                }
            }
            if (score > maxScore) {
                maxScore = score;
                bestMatch = item;
            }
        }

        let responseText = "";
        if (maxScore > 0 && bestMatch) {
            responseText = bestMatch.answer;
        } else {
            responseText = "I am the Chinmaya Ramalaya Voice Guide. You can ask me about Sunday Bala Vihar class timings, temple location in Harleysville, Yoga registration, or how to donate.";
        }

        if (this.agentResponseEl) {
            this.agentResponseEl.textContent = responseText;
        }

        this.speakResponse(responseText);
    }

    speakResponse(text) {
        if (!this.synth) return;

        if (this.synth.speaking) {
            this.synth.cancel();
        }

        // Clean speech text for natural human cadence
        let spokenText = text
            .replace(/Hari Om!\s*/gi, '') // Remove repetitive Hari Om
            .replace(/9:00 AM/g, '9 AM')
            .replace(/10:30 AM/g, '10 30 AM')
            .replace(/11:00 AM/g, '11 AM')
            .replace(/12:30 PM/g, '12 30 PM')
            .replace(/\bPA\b/g, 'Pennsylvania');

        const utterance = new SpeechSynthesisUtterance(spokenText);
        utterance.rate = 1.0; // Natural conversational tempo
        utterance.pitch = 1.0; // Natural voice pitch

        // Select chosen or best voice
        const selectedVoiceName = this.voiceSelect ? this.voiceSelect.value : '';
        const voices = this.synth.getVoices();
        
        let voice = voices.find(v => v.name === selectedVoiceName);
        if (!voice) {
            voice = voices.find(v => v.name.includes('Google US English') || v.name.includes('Google UK English') || v.name.includes('Natural') || v.lang.includes('en-IN') || v.lang.includes('en-US'));
        }

        if (voice) {
            utterance.voice = voice;
        }

        utterance.onstart = () => {
            this.isSpeaking = true;
            this.updateStatus('Speaking response...', true);
        };

        utterance.onend = () => {
            this.isSpeaking = false;
            this.updateStatus('Tap microphone to speak or type a question below.', false);
        };

        utterance.onerror = (e) => {
            console.error('Speech Synthesis error:', e);
            this.isSpeaking = false;
            this.updateStatus('Ready.', false);
        };

        this.synth.speak(utterance);
    }

    /* ----------------------------------------------------------------------
       AUDIO VISUALIZER ANIMATION (Canvas Sine Wave)
       ---------------------------------------------------------------------- */
    initVisualizer() {
        if (!this.canvas || !this.ctx) return;

        const resize = () => {
            this.canvas.width = this.canvas.parentElement.clientWidth;
            this.canvas.height = 80;
        };
        resize();
        window.addEventListener('resize', resize);

        let step = 0;
        const render = () => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            if (this.isListening || this.isSpeaking) {
                step += 0.08;
                const width = this.canvas.width;
                const height = this.canvas.height;
                const centerY = height / 2;

                // Draw 3 layered sine waves
                const waves = [
                    { color: 'rgba(179, 126, 20, 0.7)', amplitude: 22, frequency: 0.02, speed: step },
                    { color: 'rgba(112, 0, 0, 0.5)', amplitude: 16, frequency: 0.03, speed: step * 1.3 },
                    { color: 'rgba(179, 126, 20, 0.3)', amplitude: 10, frequency: 0.015, speed: step * 0.7 }
                ];

                waves.forEach(wave => {
                    this.ctx.beginPath();
                    this.ctx.lineWidth = 2.5;
                    this.ctx.strokeStyle = wave.color;

                    for (let x = 0; x < width; x++) {
                        const y = centerY + Math.sin(x * wave.frequency + wave.speed) * wave.amplitude * Math.sin(x / width * Math.PI);
                        if (x === 0) this.ctx.moveTo(x, y);
                        else this.ctx.lineTo(x, y);
                    }
                    this.ctx.stroke();
                });
            }

            this.animFrameId = requestAnimationFrame(render);
        };

        render();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.ramalayaAgent = new RamalayaAudioAgent();
});
