(ns hello-abnf.core
  (:require [instaparse.core :as insta]))

(def phone-uri-parser
  (insta/parser "https://raw.githubusercontent.com/Engelberg/instaparse/master/test/data/phone_uri.txt"
                :input-format :abnf))

;; (insta/parser (slurp "resources/phone_uri.txt") :input-format :abnf)

(phone-uri-parser "tel:+1-201-555-0123")
;; => [:telephone-uri "tel:" [:telephone-subscriber [:global-number [:global-number-digits "+" [:DIGIT "1"] [:phonedigit [:visual-separator "-"]] [:phonedigit [:DIGIT "2"]] [:phonedigit [:DIGIT "0"]] [:phonedigit [:DIGIT "1"]] [:phonedigit [:visual-separator "-"]] [:phonedigit [:DIGIT "5"]] [:phonedigit [:DIGIT "5"]] [:phonedigit [:DIGIT "5"]] [:phonedigit [:visual-separator "-"]] [:phonedigit [:DIGIT "0"]] [:phonedigit [:DIGIT "1"]] [:phonedigit [:DIGIT "2"]] [:phonedigit [:DIGIT "3"]]]]]]

;; flags: 1 byte; first two bits contain the size of auxiliary field, third bit indicates whether the signature is present.

;; auxiliary field: up to 4 bytes; contains the size of payload.

;; payload: byte array of arbitrary size (may be zero).

;; padding: byte array of arbitrary size (may be zero).

;; signature: 65 bytes, if present.

;; XXX: arbitrary size seems bad
(def whisper-envelope-parser
  (insta/parser "

whisper-envelope = expiry ttl topic data nonce

; UNIX time in seconds
expiry           = 4*4bytes

; time-to-live in seconds
ttl              = 4*4bytes

topic            = 4*4bytes

; contains encrypted message
data             = *bytes

; used for PoW calculation
nonce            = 8*8bytes

bytes = OCTET

;; first two bits contain the size of auxiliary field, third bit indicates whether the signature is present.
flags = bytes

;; contains size of payload
auxiliary-field = *4bytes

payload = *bytes

padding = *bytes

signature = 65*65bytes

;packet-code = %x30-33

" :input-format :abnf))

;; See envelope.nim and envelope.nim.out
;;env0 = Envelope(expiry:100000, ttl: 30, topic: [byte 0, 0, 0, 0],data: repeat(byte 9, 256), nonce: 1010101)

;; XXX: This isn't going to work because we don't have RLP logic setup, in principle though
(whisper-envelope-parser
"f90111830186a01e8400000000b9010009090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909090909830f69b5")
;; [:whisper-envelope [:expiry [:bytes [:OCTET "f"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "1"]]] [:ttl [:bytes [:OCTET "1"]] [:bytes [:OCTET "1"]] [:bytes [:OCTET "8"]] [:bytes [:OCTET "3"]]] [:topic [:bytes [:OCTET "0"]] [:bytes [:OCTET "1"]] [:bytes [:OCTET "8"]] [:bytes [:OCTET "6"]]] [:data [:bytes [:OCTET "a"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "1"]] [:bytes [:OCTET "e"]] [:bytes [:OCTET "8"]] [:bytes [:OCTET "4"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "b"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "1"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "9"]]] [:nonce [:bytes [:OCTET "8"]] [:bytes [:OCTET "3"]] [:bytes [:OCTET "0"]] [:bytes [:OCTET "f"]] [:bytes [:OCTET "6"]] [:bytes [:OCTET "9"]] [:bytes [:OCTET "b"]] [:bytes [:OCTET "5"]]]]

(def waku-parser

  (insta/parser (slurp "resources/waku.txt") :input-format :abnf)

  )

;; XXX: Should this encode RLP stuff?
(waku-parser "[ 0 ]")

;; example

(comment

  (insta/parser "
bytes = *OCTET
packet-code = %x30-33
" :input-format :abnf)

  bytes = OCTET*
  OCTET = #"[\u0000-\u00FF]"
  packet-code = %x0030-0033

  ;; SP is 20
  ;;[\\u0000-\\u00FF]"

  ;; parse as packet-code, how?
  (waku-parser "0")

  (waku-parser "\u0030")

  (waku-parser "\u0030\u0020")


  (waku-parser "0"[\u0000]"")


  bytes = OCTET
  OCTET = #"[\u0000-\u00FF]"


  ;; matches first thing
  (
   (insta/parser "
packet-code = 3DIGIT
; 0-127 packet codes are reserved
bytes = *OCTET" :input-format :abnf)

   "127")

  )

;; ABNF self-evaluating terminals example
;; http://zguide.zeromq.org/py:chapter7
(def ex (insta/parser "
nom-protocol    = open-peering *use-peering

open-peering    = ':C-OHAI' ( ':S-OHAI-OK' / ':S-WTF' )

use-peering     = ':C-ICANHAZ'
                / ':S-CHEEZBURGER'
                / ':C-HUGZ' ':S-HUGZ-OK'
                / ':S-HUGZ' ':C-HUGZ-OK'
" :input-format :abnf))

(ex ":C-OHAI:S-OHAI-OK:C-ICANHAZ:S-CHEEZBURGER:C-HUGZ:S-HUGZ")
;; Parse error at line 1, column 49:
;; :C-OHAI:S-OHAI-OK:C-ICANHAZ:S-CHEEZBURGER:C-HUGZ:S-HUGZ
;;                                                 ^
;; Expected:
;; ":S-HUGZ-OK"

(ex ":C-OHAI:S-OHAI-OK:C-ICANHAZ:S-CHEEZBURGER:C-HUGZ:S-HUGZ-OK")
;; [:nom-protocol [:open-peering ":C-OHAI" ":S-OHAI-OK"] [:use-peering ":C-ICANHAZ"] [:use-peering ":S-CHEEZBURGER"] [:use-peering ":C-HUGZ" ":S-HUGZ-OK"]]
