is_admin(davide).
is(bottom_right, book).

+said(Person, Something) : not prohibited_goal(reply_to)
 <- .reply_to(Person, Something);
   -said(Person, Something).


+said(Person, Something) : prohibited_goal(reply_to)
 <- -said(Person, Something).

