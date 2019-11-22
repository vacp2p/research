(ns hello-abnf.core
  (:require [instaparse.core :as insta]))

(defn parse-int [s]
  (Integer. (re-find  #"\d+" s )))

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
;; [:whisper-envelope [:expiry [:bytes [:OCTET "f"]] ...and so on for a long time

(def waku-parser

  (insta/parser (slurp "resources/waku.txt") :input-format :abnf)

  )

;; XXX: Should this encode RLP stuff?
(waku-parser "[ 0 ]")

;; example

(comment

  (
  (insta/parser "
packet-code = foobar
;packet-code = %x30-33
<foobar> = 'foobar'
<bytes> = <*OCTET>
" :input-format :abnf)
   "foobar"
   )



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




((insta/parser "
packet = packet-code packet-type
<packet-type> = 1*ALPHA
<packet-code> = bytes
<bytes> = *OCTET
<ALPHA> = %x41-5A / %x61-7A
<OCTET> = %x00-FF
" :input-format :abnf)
 "0 foobar")

((insta/parser "
packet = packet-code packet-type
<packet-type> = ':packet-type'
<packet-code> = bytes
<bytes> = *OCTET
<ALPHA> = %x41-5A / %x61-7A
<OCTET> = %x00-FF
" :input-format :abnf)
 "0 :packet-type")

OCTET = #"[\u0000-\u00FF]"

(insta/parser "
packet-code = foobar
;packet-code = %x30-33
<foobar> = 'foobar'
<bytes> = <*OCTET>
" :input-format :abnf)
)


;; whisper, high level, defer to rlp

(def packet-parser
  (insta/parser "
packet        = packet-code packet-format
packet-code     = *DIGIT
<packet-format>   = 'foo'
<DIGIT> = %x30-39
" :input-format :abnf))

(insta/transform
 {:packet-code (fn [& strs] [:code (apply str strs)])}
(packet-parser "123foo"))
;; => [:packet [:code "123"] "foo"]


;; Envelope parser with self-evaluting terminal

(def envelope-parser
(insta/parser "
envelope          = <'[ '> expiry <', '> ttl <', '> topic <', '> data <', '> nonce <' ]'>
expiry            = ':expiry' / 4*4bytes ; unix time in seconds
ttl               = ':ttl'
<topic>           = ':topic'
<data>            = ':data'
<nonce>           = ':nonce'
<bytes>           = %x00-FF
" :input-format :abnf))

(defn prettify [tree]
  (let [kw-or-concat (fn [& xs]
                       (if (= (ffirst xs) \:)
                         (keyword (subs (first xs) 1))
                         (parse-int (apply str xs))))]
    (insta/transform {:expiry kw-or-concat :ttl identity #_kw-or-concat} tree)))

(prettify (envelope-parser "[ :expiry, :ttl, :topic, :data, :nonce ]"))
;; => [:envelope :expiry :ttl ":topic" ":data" ":nonce"]

(prettify (envelope-parser "[ 1234, :ttl, :topic, :data, :nonce ]"))
;; => [:envelope 1234 :ttl ":topic" ":data" ":nonce"]
