import ConfigParser
import os


def get_configs():
    home_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

    config_dir = os.path.abspath(os.path.join(home_dir, 'config', 'configs.cfg'))
    cp = ConfigParser.ConfigParser()
    cp.read(config_dir)

    env = cp.get('general', 'env')

    configs = {
        'home_dir': home_dir,
        'agent_dir': os.path.join(home_dir, cp.get(env, 'agent.dir')),
        'health_check_period': cp.getint(env, 'health.check.period'),
        'update_check_period': cp.getint(env, 'update.check.period'),
        'main_loop_period_minute': cp.getint(env, 'main.loop.period.minute'),
        'update_server_url': cp.get(env, 'update.server.url'),
        'health_check_threshold': cp.getint(env, 'health.check.threshold')
    }
    return configs
