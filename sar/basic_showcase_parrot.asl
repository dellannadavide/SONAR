
interacting_person(unknown).

+perform_reasoning
<- !start(reasoning).

+!start(reasoning) //note here there is no normative reasoning
<- !start(reasoning_and_acting);
    -perform_reasoning.

+!start(reasoning_and_acting)
<-  !reason_and_act_about_speech.

+!reason_and_act_about_speech:
    said(Something) &
    interacting_person(Person)
 <- .reply_parrot(Person, Something);
   -said(Something).


+!reason_and_act_about_speech <- true.
