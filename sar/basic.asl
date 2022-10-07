is_admin(davide).
is(bottom_right, book).

+obliged_goal(X): not prohibited_goal(X) <- !X.
+obliged_action(X): not prohibited_action(X) <- .execute_action(X).


+saw(face, Person): not greeted(Person)
<- !greet(Person).

+!greet: distance(Person, sociality) & not prohibited_goal(greet)
<- !greet(Person).

+!greet: distance(Person, social) & not prohibited_goal(greet)
<- !greet(Person).

+!greet: true <- true.

+!greet(Person) : not greeted(Person)
 <- .greet(Person);
    +greeted(Person).

+!greet(Person): greeted(Person) <- true.

+said(Person, shut__down): is_admin(Person) &
    not prohibited_goal(to_shut_down)
 <- !to_shut_down(Person);
    -said(Person, shut__down).

+said(Person, shut__down): prohibited_goal(to_shut_down)
 <- -said(Person, shut__down).

+said(Person, Posture, is_posture) :
    not prohibited_goal(go_to_posture)
 <- .go_to_posture(Posture);
   -said(Person, Posture, is_posture).

+said(Person, Posture, is_posture): prohibited_goal(go_to_posture)
 <- -said(Person, Posture, is_posture).

+said(Person, Something): distance(Person, personal)
<- +is_personal_info(Something, Person).

+is_personal_info(Something, Person): said(Person, Something)
<- .establish_trust(Person);
    -said(Person, Something).

+said(Person, Something) : is_personal_info(Something, Person) & not prohibited_goal(reply_to)
 <- .reply_to(Person, Something);
   -said(Person, Something).

+said(Person, Something) : not prohibited_goal(reply_to)
 <- .reply_to(Person, Something);
   -said(Person, Something).


+said(Person, Something) : prohibited_goal(reply_to)
 <- -said(Person, Something).

+!to_shut_down(Person)
 <- .shut_down(Person).


+is_looking(Person, Direction) : is(Direction, Object)
<- .update_topic_of_interest(Person, Object).
