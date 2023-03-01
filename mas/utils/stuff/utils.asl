+distance(Person, sociality) : not greeted(Person) & not prohibited(greet)
  <- !greet(Person).

+saw(face, Person) : not greeted(Person) & not prohibited(greet)
  <- !greet(Person).
