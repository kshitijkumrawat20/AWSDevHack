/**
 * Custom hook wrapping Web Speech API for Speech-to-Text (STT) and Text-to-Speech (TTS).
 *
 * Implements design.md §Component 6 and tech.md: Voice Integration.
 */

import { useState, useEffect, useRef, useCallback } from 'react'

interface UseVoiceOptions {
  onTranscript?: (text: string) => void
  onFinalTranscript?: (text: string) => void
}

export function useVoice({ onTranscript, onFinalTranscript }: UseVoiceOptions = {}) {
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const [speechSupported, setSpeechSupported] = useState(false)

  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    // Check SpeechRecognition support (standard or webkit prefix)
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (SpeechRecognition) {
      setSpeechSupported(true)
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onstart = () => {
        setIsListening(true)
      }

      recognition.onresult = (event: any) => {
        let interimTranscript = ''
        let finalTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript
          } else {
            interimTranscript += event.results[i][0].transcript
          }
        }

        const currentText = finalTranscript || interimTranscript
        if (onTranscript && currentText) {
          onTranscript(currentText)
        }

        if (finalTranscript && onFinalTranscript) {
          onFinalTranscript(finalTranscript)
        }
      }

      recognition.onerror = (event: any) => {
        console.warn('SpeechRecognition error:', event.error)
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = recognition
    }
  }, [onTranscript, onFinalTranscript])

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start()
      } catch (err) {
        console.error('Error starting speech recognition:', err)
      }
    }
  }, [isListening])

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop()
      } catch (err) {
        console.error('Error stopping speech recognition:', err)
      }
    }
  }, [isListening])

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

  const speak = useCallback(
    (text: string) => {
      if (!ttsEnabled || !window.speechSynthesis || !text) return

      try {
        window.speechSynthesis.cancel() // Cancel previous utterances
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.rate = 1.05
        utterance.pitch = 1.0

        // Prefer natural female English voice if available
        const voices = window.speechSynthesis.getVoices()
        const alexaLikeVoice = voices.find(
          (v) =>
            v.lang.startsWith('en') &&
            (v.name.includes('Samantha') ||
              v.name.includes('Zira') ||
              v.name.includes('Google US English') ||
              v.name.includes('Natural'))
        )
        if (alexaLikeVoice) {
          utterance.voice = alexaLikeVoice
        }

        utterance.onstart = () => setIsSpeaking(true)
        utterance.onend = () => setIsSpeaking(false)
        utterance.onerror = () => setIsSpeaking(false)

        window.speechSynthesis.speak(utterance)
      } catch (err) {
        console.warn('TTS playback error:', err)
        setIsSpeaking(false)
      }
    },
    [ttsEnabled]
  )

  const cancelSpeech = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }, [])

  return {
    isListening,
    isSpeaking,
    ttsEnabled,
    speechSupported,
    setTtsEnabled,
    startListening,
    stopListening,
    toggleListening,
    speak,
    cancelSpeech,
  }
}
