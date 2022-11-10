
//=========================   Robot's initial knowledge   ==================================

is_admin(davide).

//important because spade ignores plan failure
interacting_person(unknown).

is(bottom_right, book).
is(behind, whiteboard).
is(behind_left, frame).


// =========================   Reasoning order, belief propagation rules, and proactive behaviors  ==================================
//reasoning order
+prepare_for_next_cycle
<- !remove_previous_norms;
    !reset_role;
    -prepare_for_next_cycle.

+!remove_previous_norms
<- !remove_previous_prohibited_goals;
    !remove_previous_prohibited_actions;
    !remove_previous_obliged_goals;
    !remove_previous_obliged_actions.

+!remove_previous_prohibited_goals : prohibited_goal(X)
<- -prohibited_goal(X);
    !remove_previous_prohibited_goals.

+!remove_previous_prohibited_actions : prohibited_action(X)
<- -prohibited_action(X);
    !remove_previous_prohibited_actions.

+!remove_previous_obliged_goals : obliged_goal(X)
<- -obliged_goal(X);
    !remove_previous_obliged_goals.

+!remove_previous_obliged_actions : obliged_action(X)
<- -obliged_action(X);
    !remove_previous_obliged_actions.

+!remove_previous_prohibited_goals <- true.
+!remove_previous_prohibited_actions <- true.
+!remove_previous_obliged_goals <- true.
+!remove_previous_obliged_actions <- true.

+!reset_role
<- -+curr_role(no_role).

+perform_reasoning
<- !start(reasoning).

+!start(reasoning)
<- !start(normative_reasoning);
    !start(reasoning_and_acting);
    -perform_reasoning.

//general belief propagation rules
//infers that the visible person is the interacting person
+visible(face, Person)
<- -+interacting_person(Person).

//infers that if it is learnt during the conversation that the name of the person is Person, then that's the name of the interacting person
+person_name(Person)
<- -+interacting_person(Person);
    +greeted(Person).


//if Something has been said, and the interacting person is Person, then Person said Something
+said(Something)
<-  ?interacting_person(Person);
    -+said(Person, Something);
    -said(Something).

//similar thing for other things said
+said(Posture, is_posture)
<-  ?interacting_person(Person);
    -+said(Person, Posture, is_posture);
    -said(Posture, is_posture).

+said(Animation, is_animation)
<-  ?interacting_person(Person);
    -+said(Person, Animation, is_animation);
    -said(Animation, is_animation).

//and for other things that concern the interacting person
+is_looking(Direction)
<-  ?interacting_person(Person);
    -+is_looking(Person, Direction);
    -is_looking(Direction).


+distance(Distance_Type)
<-  ?interacting_person(Person);
    -+distance(Person, Distance_Type);
    -distance(Distance_Type).

+detected_emotion(Emotion)
<-  ?interacting_person(Person);
    -+detected_emotion(Person, Emotion);
    -detected_emotion(Emotion).


// proactive behaviors
+add_spontaneous_conversation_goal
<- !start(spontaneous_conversation).

+!start(spontaneous_conversation) :
    visible(face, Person) &
    distance(Person, sociality)
<- .trigger_spontaneous_conversation;
    -add_spontaneous_conversation_goal.

+!start(spontaneous_conversation)
<- -add_spontaneous_conversation_goal.



//=========================   Norms   ==================================
// General rules for norm adoption
//+obliged_goal(X): not prohibited_goal(X) <- !X.
//+obliged_action(X): not prohibited_action(X) <- .execute_action(X).

+!start(normative_reasoning)
<- !reason_about_permitted_commands;
    !reason_about_roles;
    !reason_about_human_emotions;
    !reason_about_greeting_norms;
    !reason_about_dialogue_obligations;
    !reason_about_dialogue_prohibitions;
    !reason_about_dialogue_start_conversation_prohibitions.

// a prohibition concerning shutting down the robot
// if the person who gave the command is not an admin
+!reason_about_permitted_commands:
    said(Person, shut__down) &
    not is_admin(Person)
<- +prohibited_goal(to_shut_down).

+!reason_about_roles:
    perceived_object(hat)
<- .set_role(subordinate).

+!reason_about_human_emotions:
    detected_emotion(X)
<- .set_human_emotion(X).

//obligations about greeting
// v1 (sociality)
+!reason_about_greeting_norms:
    visible(face, Person) &
    distance(Person, sociality)
<- +obliged_goal(greet, Person).
// v2 (social)
+!reason_about_greeting_norms:
    visible(face, Person) &
    distance(Person, social)
<- +obliged_goal(greet, Person).

//norms concerning dialogues:

+!reason_about_dialogue_obligations:
    said(Person, bye_bye)
<- +obliged_goal(goodbye, Person);
    -said(Person, bye_bye).

//it is not appropriate to change topic of conversation if the person said something
// also it is not appropriate to just be reactive while having a social conversation, instead it is appropriate to be proactive
+!reason_about_dialogue_prohibitions:
    said(Person, Something)
<- +prohibited_action(update_topic_perception);
    +prohibited_action(update_topic_of_interest);
    +prohibited_action(reply_to_reactive).

// it is not appropriate, if it's the beginning of the conversation, to directly jump a particular topic before greeting
+!reason_about_dialogue_start_conversation_prohibitions:
    obliged_goal(greet, Person) &
    not greeted(Person)
<- +prohibited_action(update_topic_perception);
    +prohibited_action(update_topic_of_interest).


//default cases
+!reason_about_permitted_commands <- true.
+!reason_about_human_emotions <- true.
+!reason_about_roles <- true.
+!reason_about_greeting_norms <- true.
+!reason_about_dialogue_prohibitions <- true.
+!reason_about_dialogue_obligations <- true.
+!reason_about_dialogue_start_conversation_prohibitions <- true.


//=========================   Rules of behavior   ==================================

// Rules of behavior to be triggered after beliefs are added
// (i.e., after belief start(reasoning_and_acting) is added)
+!start(reasoning_and_acting)
<- !reason_and_act_about_greeting;
    !reason_and_act_about_commands;
    !reason_and_act_about_posture;
    !reason_and_act_about_interest;
    !reason_and_act_about_perceived_objects;
    !reason_and_act_about_trust;
    !reason_and_act_about_speech.


// ==== Greeting rules ====
// they create a goal to greet a person Person,
// when Person is seen at a social distance
// and the person has not been greeted already
// and it is not prohibited to greet


+!reason_and_act_about_greeting:
    obliged_goal(greet, Person)  &
    not prohibited_goal(greet)
<- !greet(Person);
    -obliged_goal(greet, Person).

+!reason_and_act_about_greeting:
    visible(face, Person) &
    not greeted(Person) &
    not prohibited_goal(greet)
<- !greet(Person).

+!reason_and_act_about_greeting:
    obliged_goal(goodbye, Person) &
    not prohibited_goal(goodbye)
<- !goodbye(Person);
    -obliged_goal(goodbye, Person).

// executes action .greet (from python)
// and adds belief greeted
+!greet(Person) : not greeted(Person)
<- +greeted(Person);
   .greet(Person).

+!greet(Person) <- true.


+!goodbye(Person)
<- .goodbye(Person).

+!goodbye(Person) <- true.

// === Commands rules ===
// they create goals based on the commands given by the user
// and based on the permissions

// Shut down
+!reason_and_act_about_commands:
    said(Person, shut__down) &
    not prohibited_goal(to_shut_down)
 <- !to_shut_down(Person);
    -said(Person, shut__down).

+!reason_and_act_about_commands:
    said(Person, shut__down) &
    prohibited_goal(to_shut_down)
 <- -said(Person, shut__down).


 +!to_shut_down(Person)
 <- .shut_down(Person).

+!reason_and_act_about_commands:
    said(Person, tell__me__what__you__know) &
    not prohibited_goal(to_tell_beliefs)
<- -said(Person, tell__me__what__you__know);
    !tell_beliefs(tellbel).

+!reason_and_act_about_commands:
    said(Person, tell__me__what__you__know) &
    prohibited_goal(to_tell_beliefs)
<- -said(Person, tell__me__what__you__know).

+!tell_beliefs(X)
<- .tell_beliefs(X).

+!reason_and_act_about_commands:
    said(Person, tell_what_you_see) &
    not prohibited_goal(tell_what_you_see)
<- -said(Person, tell_what_you_see);
    !tell_what_you_see.

+!reason_and_act_about_commands:
    said(Person, tell_what_you_see) &
    prohibited_goal(tell_what_you_see)
<- -said(Person, tell_what_you_see).

+!tell_what_you_see
<- .tell_what_you_see.

// Go to posture or animations
+!reason_and_act_about_posture:
    said(Person, Posture, is_posture) &
    not prohibited_goal(go_to_posture)
 <- .go_to_posture(Posture);
   -said(Person, Posture, is_posture).
+!reason_and_act_about_posture:
    said(Person, Posture, is_posture) &
    prohibited_goal(go_to_posture)
 <- -said(Person, Posture, is_posture).

 +!reason_and_act_about_posture:
    said(Person, Animation, is_animation) &
    not prohibited_goal(play_animation)
 <- .play_animation(Animation);
   -said(Person, Animation, is_animation).
+!reason_and_act_about_posture:
    said(Person, Animation, is_animation) &
    prohibited_goal(play_animation)
 <- -said(Person, Animation, is_animation).

// === Rules about context awareness
+!reason_and_act_about_perceived_objects:
    perceived_object(Object) &
    not prohibited_action(update_topic_perception)
<- .update_topic_perception(Object).

// === Rules to give social interpretation to inputs and act accordingly

// Change the topic of conversation if interested in something is detected
+!reason_and_act_about_interest:
    is_looking(Person, Direction) &
    not prohibited_action(move_head)
<- .move_head(Direction).

+!reason_and_act_about_interest:
    is_looking(Person, Direction) &
    is(Direction, Object) &
    not prohibited_action(update_topic_of_interest)
<- .update_topic_of_interest(Person, Object, Direction).

// establish trust if the person says something that is interpreted as personal
+!reason_and_act_about_trust:
    said(Person, Something) &
    distance(Person, personal)
<- +is_personal_info(Something, Person).

+is_personal_info(Something, Person):
    said(Person, Something) &
    not prohibited_action(establish_trust)
<- .establish_trust(Person).
//note the last rule does not delete the "said" belief, so the next can still apply


// === rules to just reply ===
+!reason_and_act_about_speech:
    said(Person, Something) &
    not prohibited_action(reply_to_reactive)
 <- .reply_to_reactive(Person, Something);
   -said(Person, Something).

// === Rules to reply in a proactive way ===
+!reason_and_act_about_speech:
    said(Person, Something) &
    not prohibited_action(reply_to_proactive)
<- .reply_to_proactive(Person, Something);
   -said(Person, Something).

//default cases, just ignoring what has been said
+!reason_and_act_about_speech:
    said(Person, Something)
 <- -said(Person, Something).

//default cases
+!reason_and_act_about_greeting <- true.
+!reason_and_act_about_commands <- true.
+!reason_and_act_about_posture <- true.
+!reason_and_act_about_interest <- true.
+!reason_and_act_about_perceived_objects <- true.
+!reason_and_act_about_trust <- true.
+!reason_and_act_about_speech <- true.

// Rules for beliefs removal
//+remove_belief(X) <- !tell_beliefs(removeX_beginning); -X; !tell_beliefs(removeX_afterremoval); -remove_belief(X); !tell_beliefs(removeX_afterremovalofremove).
//+remove_belief(X, Y) <- !tell_beliefs(removeXY_beginning); -X(Y); !tell_beliefs(removeXY_afterremoval); -remove_belief(X, Y); !tell_beliefs(removeXY_afterremovalofremove).
