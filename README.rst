structspec
==========

*A language-independent, platform-neutral way of specifying binary packet structures.*

Introduction
------------

Imagine you're working in a multiple-person project that makes use of more than one language and
perhaps spans multiple hardware platforms, and that you need to pass binary packets across
different components. When these components are owned by the same developer, reside on the same
hardware, and are written in the same language, it's not a problem. When one or more of these
assertions is no longer true it becomes more problematic. It becomes worse still when the formats
of these packets change, and the more they change the worse it gets.

Wouldn't it be nice to have an easy, neutral way to specify the formats of these binary structures
and have some basic tools help do some of the grunt work with them in different languages so that
when they change it doesn't cause everything everywhere to break?

That's what structspec is all about.
