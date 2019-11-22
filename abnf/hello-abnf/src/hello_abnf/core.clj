(ns hello-abnf.core
  (:require [instaparse.core :as insta]))

(def phone-uri-parser
  (insta/parser "https://raw.githubusercontent.com/Engelberg/instaparse/master/test/data/phone_uri.txt"
                :input-format :abnf))

(phone-uri-parser "tel:+1-201-555-0123")
;; => [:telephone-uri "tel:" [:telephone-subscriber [:global-number [:global-number-digits "+" [:DIGIT "1"] [:phonedigit [:visual-separator "-"]] [:phonedigit [:DIGIT "2"]] [:phonedigit [:DIGIT "0"]] [:phonedigit [:DIGIT "1"]] [:phonedigit [:visual-separator "-"]] [:phonedigit [:DIGIT "5"]] [:phonedigit [:DIGIT "5"]] [:phonedigit [:DIGIT "5"]] [:phonedigit [:visual-separator "-"]] [:phonedigit [:DIGIT "0"]] [:phonedigit [:DIGIT "1"]] [:phonedigit [:DIGIT "2"]] [:phonedigit [:DIGIT "3"]]]]]]
