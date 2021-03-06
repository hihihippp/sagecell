"""
Permalink web server

This Tornado server provides a permalink service with a convenient
post/get api for storing and retrieving code.
"""

import tornado.httpserver
import tornado.ioloop
import tornado.web
import os
import misc
import permalink

class PermalinkServer(tornado.web.Application):
    def __init__(self):
        handlers_list = [
            (r"/", permalink.PermalinkHandler),
            (r"/permalink", permalink.PermalinkHandler),
            ]
        self.config = misc.Config()
        db = __import__('db_'+self.config.get_config('permalink_server')['db'])
        self.db = db.DB(self.config.get_config('permalink_server')['db_config']['uri'])

        #self.ioloop = ioloop.IOLoop.instance()
        # to check for blocking when debugging, uncomment the following
        # and set the argument to the blocking timeout in seconds 
        #self.ioloop.set_blocking_log_threshold(.5)

        super(PermalinkServer, self).__init__(handlers_list)

if __name__ == "__main__":
    import tornado.options
    from tornado.options import define, options

    define("port", default=8889, help="run on the given port", type=int)
    tornado.options.parse_command_line()

    import lockfile
    from lockfile.pidlockfile import PIDLockFile
    config = misc.Config()
    pidfile_path = config.get_config('permalink_pid_file')
    pidlock = PIDLockFile(pidfile_path)
    if pidlock.is_locked():
        # try killing the process that has the lock
        pid = pidlock.read_pid()
        print "Killing PID %d"%pid
        try:
            os.kill(pid, 9)
        except OSError, (code, text):
            import errno
            if code != errno.ESRCH:
                raise
            else:
                # process doesn't exist anymore
                print "Old process %d already gone"%pid
                pidlock.break_lock()
    try:
        pidlock.acquire(timeout=10)
        application = PermalinkServer()
        http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    finally:
        pidlock.release()

