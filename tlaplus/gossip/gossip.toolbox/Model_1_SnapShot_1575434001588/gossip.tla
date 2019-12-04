------------------------------- MODULE gossip -------------------------------

EXTENDS Integers

(*--algorithm gossip
variables
    nodes = {"alice", "bob", "charlie"},
    peers = [n \in nodes |-> "charlie"],
    inbox = [n \in nodes |-> 0],
    sender = "alice",
    receiver = "bob",
    amount = 4;

define
    IsSpread == \A n \in nodes: inbox[n] > 0
end define;

begin
    Send:
        inbox[sender] := inbox[sender] + 1;
        Propagate:
            inbox[peers[sender]] := inbox[peers[sender]] + 1;
end algorithm;*)

\* BEGIN TRANSLATION
VARIABLES nodes, peers, inbox, sender, receiver, amount, pc

(* define statement *)
IsSpread == \A n \in nodes: inbox[n] > 0


vars == << nodes, peers, inbox, sender, receiver, amount, pc >>

Init == (* Global variables *)
        /\ nodes = {"alice", "bob", "charlie"}
        /\ peers = [n \in nodes |-> "charlie"]
        /\ inbox = [n \in nodes |-> 0]
        /\ sender = "alice"
        /\ receiver = "bob"
        /\ amount = 4
        /\ pc = "Send"

Send == /\ pc = "Send"
        /\ inbox' = [inbox EXCEPT ![sender] = inbox[sender] + 1]
        /\ pc' = "Propagate"
        /\ UNCHANGED << nodes, peers, sender, receiver, amount >>

Propagate == /\ pc = "Propagate"
             /\ inbox' = [inbox EXCEPT ![peers[sender]] = inbox[peers[sender]] + 1]
             /\ pc' = "Done"
             /\ UNCHANGED << nodes, peers, sender, receiver, amount >>

Next == Send \/ Propagate
           \/ (* Disjunct to prevent deadlock on termination *)
              (pc = "Done" /\ UNCHANGED vars)

Spec == Init /\ [][Next]_vars

Termination == <>(pc = "Done")

\* END TRANSLATION

=============================================================================
