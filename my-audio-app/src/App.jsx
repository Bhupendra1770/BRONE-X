// // import React, { useState, useRef } from "react";

// // export default function App() {
// //   const [recording, setRecording] = useState(false);
// //   const [status, setStatus] = useState("Idle");
// //   const socketRef = useRef(null);
// //   const mediaRecorderRef = useRef(null);
// //   const chunksRef = useRef([]);
// //   const silenceTimerRef = useRef(null);

// //   const startRecording = async () => {
// //     if (recording) return;

// //     // Connect WebSocket
// //     socketRef.current = new WebSocket("ws://localhost:8000/exotel-audio");

// //     socketRef.current.onopen = () => {
// //       console.log("Connected to WebSocket server");
// //     };

// //     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
// //     mediaRecorderRef.current = new MediaRecorder(stream, {
// //       mimeType: "audio/webm",
// //     });

// //     mediaRecorderRef.current.ondataavailable = (e) => {
// //       if (e.data.size > 0) {
// //         chunksRef.current.push(e.data);
// //       }
// //     };

// //     mediaRecorderRef.current.onstop = async () => {
// //       const blob = new Blob(chunksRef.current, { type: "audio/webm" });
// //       chunksRef.current = [];

// //       // Convert blob to base64
// //       const reader = new FileReader();
// //       reader.onloadend = () => {
// //         const base64Data = reader.result.split(",")[1];
// //         socketRef.current.send(base64Data);
// //         console.log("Sent complete audio file to WebSocket");
// //       };
// //       reader.readAsDataURL(blob);
// //     };

// //     mediaRecorderRef.current.start();
// //     detectSilence(stream);

// //     setRecording(true);
// //     setStatus("Recording...");
// //   };

// //   const stopRecording = () => {
// //     if (mediaRecorderRef.current && recording) {
// //       mediaRecorderRef.current.stop();
// //       setRecording(false);
// //       setStatus("Stopped");
// //     }
// //   };

// //   // --- Silence Detection (3 seconds of silence) ---
// //   const detectSilence = (stream) => {
// //     const audioContext = new AudioContext();
// //     const source = audioContext.createMediaStreamSource(stream);
// //     const analyser = audioContext.createAnalyser();
// //     const data = new Uint8Array(analyser.fftSize);

// //     source.connect(analyser);

// //     const checkSilence = () => {
// //       analyser.getByteTimeDomainData(data);
// //       let silent = true;

// //       for (let i = 0; i < data.length; i++) {
// //         if (Math.abs(data[i] - 128) > 5) {
// //           silent = false;
// //           break;
// //         }
// //       }

// //       if (silent) {
// //         if (!silenceTimerRef.current) {
// //           silenceTimerRef.current = setTimeout(() => {
// //             console.log("3 seconds silence detected, stopping recording...");
// //             stopRecording();
// //             silenceTimerRef.current = null;
// //           }, 3000);
// //         }
// //       } else {
// //         if (silenceTimerRef.current) {
// //           clearTimeout(silenceTimerRef.current);
// //           silenceTimerRef.current = null;
// //         }
// //       }

// //       requestAnimationFrame(checkSilence);
// //     };

// //     checkSilence();
// //   };

// //   return (
// //     <div style={{ padding: "20px", fontFamily: "Arial" }}>
// //       <h1>🎙️ Real-time Audio Recorder</h1>
// //       <p>Status: {status}</p>
// //       <button onClick={startRecording} disabled={recording}>
// //         Start Recording
// //       </button>
// //       <button onClick={stopRecording} disabled={!recording}>
// //         Stop Recording
// //       </button>
// //     </div>
// //   );
// // }




// import React, { useEffect, useRef, useState } from "react";

// export default function App() {
//   const [status, setStatus] = useState("Idle");
//   const socketRef = useRef(null);
//   const mediaRecorderRef = useRef(null);
//   const chunksRef = useRef([]);
//   const silenceTimerRef = useRef(null);
//   const listeningRef = useRef(false);

//   useEffect(() => {
//     // Connect WebSocket once
//     socketRef.current = new WebSocket("ws://localhost:8000/exotel-audio");

//     socketRef.current.onopen = () => {
//       console.log("Connected to WebSocket server");
//     };

//     startMicrophone();
//   }, []);

//   const startMicrophone = async () => {
//     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//     detectVoice(stream);
//   };

//   const startRecording = (stream) => {
//     if (listeningRef.current) return; // already recording
//     listeningRef.current = true;

//     mediaRecorderRef.current = new MediaRecorder(stream, {
//       mimeType: "audio/webm",
//     });

//     mediaRecorderRef.current.ondataavailable = (e) => {
//       if (e.data.size > 0) {
//         chunksRef.current.push(e.data);
//       }
//     };

//     mediaRecorderRef.current.onstop = () => {
//       if (chunksRef.current.length === 0) return;

//       const blob = new Blob(chunksRef.current, { type: "audio/webm" });
//       chunksRef.current = [];

//       // Convert to base64 and send
//       const reader = new FileReader();
//       reader.onloadend = () => {
//         const base64Data = reader.result.split(",")[1];
//         socketRef.current.send(base64Data);
//         console.log("📤 Sent complete audio file to WebSocket");
//       };
//       reader.readAsDataURL(blob);
//     };

//     mediaRecorderRef.current.start();
//     setStatus("🎙️ Recording...");
//     console.log("Recording started");
//   };

//   const stopRecording = () => {
//     if (mediaRecorderRef.current && listeningRef.current) {
//       mediaRecorderRef.current.stop();
//       listeningRef.current = false;
//       setStatus("Idle, waiting for voice...");
//       console.log("Recording stopped, file will be sent");
//     }
//   };

//   const detectVoice = (stream) => {
//     const audioContext = new AudioContext();
//     const source = audioContext.createMediaStreamSource(stream);
//     const analyser = audioContext.createAnalyser();
//     const data = new Uint8Array(analyser.fftSize);

//     source.connect(analyser);

//     const checkVoice = () => {
//       analyser.getByteTimeDomainData(data);
//       let talking = false;

//       for (let i = 0; i < data.length; i++) {
//         if (Math.abs(data[i] - 128) > 10) { // threshold
//           talking = true;
//           break;
//         }
//       }

//       if (talking) {
//         if (!listeningRef.current) {
//           console.log("Voice detected → start recording");
//           startRecording(stream);
//         }
//         if (silenceTimerRef.current) {
//           clearTimeout(silenceTimerRef.current);
//           silenceTimerRef.current = null;
//         }
//       } else {
//         if (listeningRef.current && !silenceTimerRef.current) {
//           silenceTimerRef.current = setTimeout(() => {
//             console.log("Silence detected → stop recording");
//             stopRecording();
//             silenceTimerRef.current = null;
//           }, 3000); // 3 seconds silence
//         }
//       }

//       requestAnimationFrame(checkVoice);
//     };

//     checkVoice();
//   };

//   return (
//     <div style={{ padding: "20px", fontFamily: "Arial" }}>
//       <h1>🎙️ Voice Activated Recorder</h1>
//       <p>Status: {status}</p>
//       <p>👉 Starts recording when you talk, stops after 3s silence.</p>
//     </div>
//   );
// }





















// import React, { useEffect, useRef, useState } from "react";

// export default function App() {
//   const [status, setStatus] = useState("Idle");
//   const socketRef = useRef(null);
//   const mediaRecorderRef = useRef(null);
//   const chunksRef = useRef([]);
//   const silenceTimerRef = useRef(null);
//   const listeningRef = useRef(false);
//   const audioPlayerRef = useRef(null); // 🔊 for playback

//   useEffect(() => {
//     // Connect WebSocket
//     socketRef.current = new WebSocket("ws://localhost:8000/exotel-audio");

//     socketRef.current.onopen = () => {
//       console.log("✅ Connected to WebSocket server");
//     };

//     // 🔊 Handle audio coming back from server
//     socketRef.current.onmessage = (event) => {
//       if (typeof event.data === "string" && event.data.startsWith("AUDIO:")) {
//         const base64Audio = event.data.replace("AUDIO:", "");
//         const audioBlob = base64ToBlob(base64Audio, "audio/webm");
//         const audioUrl = URL.createObjectURL(audioBlob);

//         if (audioPlayerRef.current) {
//           audioPlayerRef.current.pause();
//           audioPlayerRef.current.currentTime = 0;
//         }

//         audioPlayerRef.current = new Audio(audioUrl);
//         audioPlayerRef.current.play()
//           .then(() => console.log("🔊 Playing server audio"))
//           .catch((err) => console.error("Audio play failed:", err));
//       }
//     };

//     startMicrophone();
//   }, []);

//   // Convert base64 → Blob
//   const base64ToBlob = (base64, mime) => {
//     const byteChars = atob(base64);
//     const byteNumbers = new Array(byteChars.length);
//     for (let i = 0; i < byteChars.length; i++) {
//       byteNumbers[i] = byteChars.charCodeAt(i);
//     }
//     const byteArray = new Uint8Array(byteNumbers);
//     return new Blob([byteArray], { type: mime });
//   };

//   const startMicrophone = async () => {
//     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//     detectVoice(stream);
//   };

//   const startRecording = (stream) => {
//     if (listeningRef.current) return; // already recording
//     listeningRef.current = true;

//     if (audioPlayerRef.current) {
//       audioPlayerRef.current.pause(); // 🔇 Stop playback when user talks
//     }

//     mediaRecorderRef.current = new MediaRecorder(stream, {
//       mimeType: "audio/webm",
//     });

//     mediaRecorderRef.current.ondataavailable = (e) => {
//       if (e.data.size > 0) {
//         chunksRef.current.push(e.data);
//       }
//     };

//     mediaRecorderRef.current.onstop = () => {
//       if (chunksRef.current.length === 0) return;

//       const blob = new Blob(chunksRef.current, { type: "audio/webm" });
//       chunksRef.current = [];

//       // Convert to base64 and send
//       const reader = new FileReader();
//       reader.onloadend = () => {
//         const base64Data = reader.result.split(",")[1];
//         socketRef.current.send(base64Data);
//         console.log("📤 Sent complete audio file to WebSocket");
//       };
//       reader.readAsDataURL(blob);
//     };

//     mediaRecorderRef.current.start();
//     setStatus("🎙️ Recording...");
//     console.log("Recording started");
//   };

//   const stopRecording = () => {
//     if (mediaRecorderRef.current && listeningRef.current) {
//       mediaRecorderRef.current.stop();
//       listeningRef.current = false;
//       setStatus("Idle, waiting for voice...");
//       console.log("Recording stopped, file will be sent");
//     }
//   };

//   const detectVoice = (stream) => {
//     const audioContext = new AudioContext();
//     const source = audioContext.createMediaStreamSource(stream);
//     const analyser = audioContext.createAnalyser();
//     analyser.fftSize = 2048;
//     const data = new Uint8Array(analyser.fftSize);

//     source.connect(analyser);

//     const checkVoice = () => {
//       analyser.getByteTimeDomainData(data);
//       let talking = false;

//       for (let i = 0; i < data.length; i++) {
//         if (Math.abs(data[i] - 128) > 15) { // 🔼 Increased threshold
//           talking = true;
//           break;
//         }
//       }

//       if (talking) {
//         if (!listeningRef.current) {
//           console.log("🎤 Voice detected → start recording");
//           startRecording(stream);
//         }
//         if (silenceTimerRef.current) {
//           clearTimeout(silenceTimerRef.current);
//           silenceTimerRef.current = null;
//         }
//       } else {
//         if (listeningRef.current && !silenceTimerRef.current) {
//           silenceTimerRef.current = setTimeout(() => {
//             console.log("🤫 Silence detected → stop recording");
//             stopRecording();
//             silenceTimerRef.current = null;
//           }, 2500); // shorter silence cutoff
//         }
//       }

//       requestAnimationFrame(checkVoice);
//     };

//     checkVoice();
//   };

//   return (
//     <div style={{ padding: "20px", fontFamily: "Arial" }}>
//       <h1>🎙️ Voice Assistant</h1>
//       <p>Status: {status}</p>
//       <p>👉 Starts recording when you talk, stops after silence.</p>
//     </div>
//   );
// }















import React, { useEffect, useRef, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("Idle");
  const [volumeLevel, setVolumeLevel] = useState(0);
  const socketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const listeningRef = useRef(false);
  const audioPlayerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);
  const filteredStreamRef = useRef(null); // Filtered audio stream for recording
  const noiseGateRef = useRef(0); // Track noise floor
  const consecutiveVoiceFramesRef = useRef(0); // Require multiple frames for voice detection

  useEffect(() => {
    // Connect WebSocket once
    socketRef.current = new WebSocket("ws://localhost:8000/exotel-audio");

    socketRef.current.onopen = () => {
      console.log("✅ Connected to WebSocket server");
    };

    socketRef.current.onerror = (error) => {
      console.error("⚠️ WebSocket error:", error);
      setStatus("❌ Connection error");
    };

    socketRef.current.onclose = () => {
      console.log("⚠️ WebSocket closed");
      setStatus("❌ Disconnected");
    };

    // When server sends audio back
    socketRef.current.onmessage = async (event) => {
      try {
        // stop listening if audio is coming in
        if (mediaRecorderRef.current && listeningRef.current) {
          stopRecording();
        }

        let audioBlob;

        if (typeof event.data === "string") {
          // JSON message with base64
          const msg = JSON.parse(event.data);
          if (msg.audio_base64) {
            const audioBytes = Uint8Array.from(atob(msg.audio_base64), c =>
              c.charCodeAt(0)
            );
            audioBlob = new Blob([audioBytes], { type: "audio/webm" });
          }
        } else {
          // raw binary from server
          const arrayBuffer = await event.data.arrayBuffer();
          audioBlob = new Blob([arrayBuffer], { type: "audio/webm" });
        }

        if (audioBlob) {
          const url = URL.createObjectURL(audioBlob);

          if (audioPlayerRef.current) {
            audioPlayerRef.current.pause();
          }

          audioPlayerRef.current = new Audio(url);
          audioPlayerRef.current.onended = () => {
            console.log("✅ Finished playing server audio");
            setStatus("Idle, waiting for voice...");
            URL.revokeObjectURL(url);
          };

          await audioPlayerRef.current.play();
          setStatus("🔊 Playing response...");
          console.log("🎵 Playing server audio");
        }
      } catch (err) {
        console.error("⚠️ Error handling server audio:", err);
      }
    };

    startMicrophone();

    return () => {
      // Cleanup
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const startMicrophone = async () => {
    try {
      // Request microphone with noise suppression and echo cancellation
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
          channelCount: 1,
          // Request high quality audio for better processing
          latency: 0.01
        }
      });
      
      streamRef.current = stream;
      setupAudioProcessing(stream);
    } catch (err) {
      console.error("❌ Error accessing microphone:", err);
      setStatus("❌ Microphone access denied");
    }
  };

  const setupAudioProcessing = (stream) => {
    // Create audio context
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    audioContextRef.current = audioContext;

    // Create source from stream
    const source = audioContext.createMediaStreamSource(stream);
    sourceRef.current = source;

    // Create analyser for frequency analysis
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048; // Higher FFT size for better frequency resolution
    analyser.smoothingTimeConstant = 0.8;
    analyserRef.current = analyser;

    // Create high-pass filter to remove low-frequency noise (below 80Hz)
    const highPassFilter = audioContext.createBiquadFilter();
    highPassFilter.type = "highpass";
    highPassFilter.frequency.value = 80; // Human speech starts around 85Hz

    // Create low-pass filter to remove high-frequency noise (above 8kHz)
    const lowPassFilter = audioContext.createBiquadFilter();
    lowPassFilter.type = "lowpass";
    lowPassFilter.frequency.value = 8000; // Human speech typically below 8kHz

    // Create destination for filtered audio stream (for recording)
    const destination = audioContext.createMediaStreamDestination();
    filteredStreamRef.current = destination.stream;

    // Connect: source -> highpass -> lowpass -> analyser (for detection)
    // Also connect: source -> highpass -> lowpass -> destination (for recording)
    source.connect(highPassFilter);
    highPassFilter.connect(lowPassFilter);
    lowPassFilter.connect(analyser); // For voice detection
    lowPassFilter.connect(destination); // For recording filtered audio

    // Calibrate noise floor (first 1 second)
    calibrateNoiseFloor(analyser, () => {
      detectVoice(stream, analyser);
    });
  };

  const calibrateNoiseFloor = (analyser, callback) => {
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const timeData = new Uint8Array(analyser.fftSize);
    let samples = 0;
    let totalNoise = 0;
    const calibrationDuration = 1000; // 1 second
    const startTime = Date.now();

    const calibrate = () => {
      if (Date.now() - startTime < calibrationDuration) {
        analyser.getByteFrequencyData(dataArray);
        analyser.getByteTimeDomainData(timeData);
        
        // Calculate RMS for noise floor
        let sum = 0;
        for (let i = 0; i < timeData.length; i++) {
          const normalized = (timeData[i] - 128) / 128;
          sum += normalized * normalized;
        }
        const rms = Math.sqrt(sum / timeData.length);
        totalNoise += rms;
        samples++;

        requestAnimationFrame(calibrate);
      } else {
        noiseGateRef.current = (totalNoise / samples) * 1.5; // Set threshold 1.5x above noise floor
        console.log("🎚️ Noise floor calibrated:", noiseGateRef.current.toFixed(4));
        setStatus("✅ Ready - Speak close to microphone");
        callback();
      }
    };

    setStatus("🔧 Calibrating noise floor...");
    calibrate();
  };

  const detectVoice = (stream, analyser) => {
    const timeData = new Uint8Array(analyser.fftSize);
    const frequencyData = new Uint8Array(analyser.frequencyBinCount);

    const checkVoice = () => {
      analyser.getByteTimeDomainData(timeData);
      analyser.getByteFrequencyData(frequencyData);

      // Calculate RMS (Root Mean Square) for amplitude
      let sum = 0;
      for (let i = 0; i < timeData.length; i++) {
        const normalized = (timeData[i] - 128) / 128;
        sum += normalized * normalized;
      }
      const rms = Math.sqrt(sum / timeData.length);
      const volume = Math.min(rms * 100, 100); // Scale to 0-100
      setVolumeLevel(volume);

      // Check for human speech frequency range (85-255 Hz fundamental, harmonics up to 8kHz)
      const speechDetected = detectHumanSpeech(frequencyData, analyser);

      // Proximity check: require higher amplitude for close microphone
      // Threshold: 0.15 RMS (adjust based on testing - higher = closer required)
      const proximityThreshold = 0.12;
      const isCloseEnough = rms > proximityThreshold;

      // Noise gate: must exceed noise floor significantly
      const exceedsNoiseGate = rms > noiseGateRef.current * 2.5;

      // Require multiple consecutive frames to avoid false positives
      if (speechDetected && isCloseEnough && exceedsNoiseGate) {
        consecutiveVoiceFramesRef.current++;
        
        // Require 3 consecutive frames (about 50ms at 60fps) to start recording
        if (consecutiveVoiceFramesRef.current >= 3) {
          if (!listeningRef.current) {
            console.log("🎤 Human speech detected (close proximity) → start recording");
            startRecording(stream);
          }
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        }
      } else {
        consecutiveVoiceFramesRef.current = 0;
        
        if (listeningRef.current && !silenceTimerRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            console.log("🤫 Silence detected → stop recording");
            stopRecording();
            silenceTimerRef.current = null;
          }, 1500); // 1.5 seconds of silence
        }
      }

      requestAnimationFrame(checkVoice);
    };

    checkVoice();
  };

  const detectHumanSpeech = (frequencyData, analyser) => {
    const sampleRate = audioContextRef.current.sampleRate;
    const binSize = sampleRate / analyser.fftSize;
    
    // Human speech fundamental frequency: 85-255 Hz (male: 85-180Hz, female: 165-255Hz)
    const speechFundamentalMin = Math.floor(85 / binSize);
    const speechFundamentalMax = Math.floor(255 / binSize);
    
    // Check for energy in speech frequency range
    let speechEnergy = 0;
    let totalEnergy = 0;
    
    for (let i = 0; i < frequencyData.length; i++) {
      const frequency = i * binSize;
      const magnitude = frequencyData[i] / 255;
      totalEnergy += magnitude;
      
      // Primary speech range: 85-8000 Hz
      if (frequency >= 85 && frequency <= 8000) {
        speechEnergy += magnitude;
      }
    }
    
    // Speech should have significant energy in the speech range
    // At least 40% of total energy should be in speech frequencies
    const speechRatio = totalEnergy > 0 ? speechEnergy / totalEnergy : 0;
    
    // Also check for fundamental frequency presence
    let fundamentalEnergy = 0;
    for (let i = speechFundamentalMin; i <= speechFundamentalMax && i < frequencyData.length; i++) {
      fundamentalEnergy += frequencyData[i] / 255;
    }
    
    // Require both: significant speech frequency content AND fundamental frequency presence
    return speechRatio > 0.4 && fundamentalEnergy > 0.1;
  };

  const startRecording = (stream) => {
    if (listeningRef.current) return;
    listeningRef.current = true;

    // Stop playback if audio is playing
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
      console.log("⏹️ Stopped playback due to voice input");
    }

    // Use the filtered stream (with noise suppression filters) for recording
    const filteredStream = filteredStreamRef.current;
    if (!filteredStream) {
      console.error("❌ Filtered stream not available");
      return;
    }

    mediaRecorderRef.current = new MediaRecorder(filteredStream, {
      mimeType: "audio/webm;codecs=opus",
      audioBitsPerSecond: 128000 // Higher quality
    });

    mediaRecorderRef.current.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };

    mediaRecorderRef.current.onstop = () => {
      if (chunksRef.current.length === 0) return;

      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      chunksRef.current = [];

      // Convert to base64 and send
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64Data = reader.result.split(",")[1];
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(base64Data);
          console.log("📤 Sent filtered audio to WebSocket");
        }
      };
      reader.readAsDataURL(blob);
    };

    mediaRecorderRef.current.start(100); // Collect data every 100ms
    setStatus("🎙️ Recording (noise filtered)...");
    console.log("🎙️ Recording started with noise suppression");
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && listeningRef.current) {
      mediaRecorderRef.current.stop();
      listeningRef.current = false;
      setStatus("Idle, waiting for voice...");
      console.log("⏹️ Recording stopped, file will be sent");
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif", maxWidth: "600px", margin: "0 auto" }}>
      <h1>🎙️ Enhanced Voice Recorder</h1>
      <div style={{ marginBottom: "20px" }}>
        <p><strong>Status:</strong> {status}</p>
        <div style={{ marginTop: "10px" }}>
          <label style={{ display: "block", marginBottom: "5px" }}>
            <strong>Volume Level:</strong> {volumeLevel.toFixed(1)}%
          </label>
          <div style={{
            width: "100%",
            height: "20px",
            backgroundColor: "#e0e0e0",
            borderRadius: "10px",
            overflow: "hidden"
          }}>
            <div style={{
              width: `${volumeLevel}%`,
              height: "100%",
              backgroundColor: volumeLevel > 15 ? "#4caf50" : "#ff9800",
              transition: "width 0.1s ease"
            }} />
          </div>
        </div>
      </div>
      <div style={{
        padding: "15px",
        backgroundColor: "#f5f5f5",
        borderRadius: "8px",
        marginTop: "20px"
      }}>
        <h3 style={{ marginTop: 0 }}>✨ Features:</h3>
        <ul style={{ lineHeight: "1.8" }}>
          <li>🎚️ <strong>Noise Suppression:</strong> Filters out background noise</li>
          <li>📏 <strong>Proximity Detection:</strong> Only records when microphone is close</li>
          <li>🗣️ <strong>Speech Recognition:</strong> Detects human speech frequencies</li>
          <li>🔇 <strong>Noise Gate:</strong> Ignores low-level ambient sounds</li>
          <li>🔊 <strong>Auto Playback:</strong> Plays server responses automatically</li>
        </ul>
        <p style={{ marginTop: "15px", fontStyle: "italic", color: "#666" }}>
          💡 <strong>Tip:</strong> Speak clearly and close to your microphone for best results.
        </p>
      </div>
    </div>
  );
}
