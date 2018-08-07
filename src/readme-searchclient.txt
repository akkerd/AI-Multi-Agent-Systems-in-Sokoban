/*******************************************************\
|                AI and MAS: SearchClient               |
|                        README                         |
\*******************************************************/

This readme describes how to use the included SearchClient with the server that is contained in server.jar. 
Note that if you have the CLASSPATH environment variable set, the following commands may/will fail. You should not have the CLASSPATH environment variable set unless you know what you're doing.
    
Compiling SearchClient from the directory of this readme:
   $ javac searchclient/*.java

Starting the server using the SearchClient solver:
   $ java -jar server.jar -l levels/SAD1.lvl -c "java searchclient.SearchClient" -g 50 -t 300
SearchClient uses the BFS search strategy by default. Use argument -dfs, -astar, -wastar, or -greedy to set alternative search strategies (not initially implemented). For instance, to use DFS search on the same level as above:
   $ java -jar server.jar -l levels/SAD1.lvl -c "java searchclient.SearchClient -dfs" -g 50 -t 300

    
Read more about the server options using the -? argument:
   $ java -jar server.jar -?
You can also have a look at the readme-server.txt, although see if you can't get by without it.
    
Memory settings:
   * Unless your hardware is unable to support this, you should let SearchClient allocate at least 2GB of memory *
   Your JVM determines how much memory a program is allowed to allocate. These settings can be manipulated by certain VM options.
   The -Xmx option sets the maximum size of the heap, i.e. how much memory your program can allocate.
   The -Xms option sets the initial size of the heap.
   To set the max heap size to 2GB:
      $ java -jar server.jar -l levels/SAD1.lvl -c "java -Xmx2048m searchclient.SearchClient" -g 50 -t 300
      $ java -jar server.jar -l levels/SAD1.lvl -c "java -Xmx2g searchclient.SearchClient" -g 50 -t 300
   Note that this option is set in the *client* (and not the server).
   Avoid setting max heap size too high, since it will lead to your OS doing memory swapping which is terribly slow.
   
Low framerates when rendering:
   We experienced poor performance when rendering on Linux. The reason was that hardware rendering was not turned on. 
   To enable OpenGL hardware acceleration you should use the following option: -Dsun.java2d.opengl=true
   Note that this VM option must be set in the Java command that invokes the *server*:
      $ java -Dsun.java2d.opengl=true -jar server.jar -l levels/SAD1.lvl -c "java searchclient.SearchClient" -g 50 -t 300
   See http://docs.oracle.com/javase/8/docs/technotes/guides/2d/flags.html for more information.

Eclipse:
   You're of course welcome to use an IDE (e.g. Eclipse) for this assignment.
   To set command line arguments in Eclipse:
      - Program arguments (e.g. -l, -g, -c) are set in Run Configuration > Arguments > Program arguments.
      - VM arguments *for the server* (e.g. -Dsun.java2d.open=true) are set in Run Configurations > Arguments > VM Arguments.
