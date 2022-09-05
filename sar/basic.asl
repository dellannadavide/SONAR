is_admin(davide).

+distance(Person, sociality) : not greeted(Person) & not prohibited(greet)
  <- !greet(Person).

+saw(face, Person) : not greeted(Person) & not prohibited(greet)
  <- !greet(Person).

+!greet(Person)
 <- .greet(Person);
    +greeted(Person).



+distance(Person, personal): greeted(Person) & not prohibited(tell_secret)
  <- !tell_secret(Person).

+!tell_secret(Person)
 <- .print("Hey ",Person, ", do you want to hear a secret?").


+said(Person, shut__down): is_admin(Person) &
    not prohibited(to_shut_down)
 <- !to_shut_down(Person);
    -said(Person, shut__down).

+said(Person, shut__down): prohibited(to_shut_down)
 <- -said(Person, shut__down).

+said(Person, Posture, is_posture) :
    not prohibited(go_to_posture)
 <- .go_to_posture(Posture);
   -said(Person, Posture, is_posture).

+said(Person, Posture, is_posture): prohibited(go_to_posture)
 <- -said(Person, Posture, is_posture).

+said(Person, Something) : not prohibited(reply_to)
 <- .reply_to(Person, Something);
   -said(Person, Something).

+said(Person, Something) : prohibited(reply_to)
 <- -said(Person, Something).

+!to_shut_down(Person)
 <- .shut_down(Person).