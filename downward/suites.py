# -*- coding: utf-8 -*-
#
# downward uses the lab package to conduct experiments with the
# Fast Downward planning system.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from lab import tools


class Domain(object):
    def __init__(self, benchmarks_dir, domain):
        self.domain = domain
        directory = os.path.join(benchmarks_dir, domain)
        problem_files = tools.natural_sort([
            p for p in os.listdir(directory) if 'domain' not in p])
        self.problems = [
            Problem(benchmarks_dir, domain, problem)
            for problem in problem_files]

    def __str__(self):
        return self.domain

    def __repr__(self):
        return '<Domain %s>' % self.domain

    def __hash__(self):
        return hash(self.domain)

    def __cmp__(self, other):
        return cmp(self.domain, other.domain)

    def __iter__(self):
        return iter(self.problems)


class Problem(object):
    def __init__(self, benchmarks_dir, domain, problem):
        self.benchmarks_dir = benchmarks_dir
        self.domain = domain
        self.problem = problem

    def __str__(self):
        return '%s:%s' % (self.domain, self.problem)

    def __repr__(self):
        return '<Problem %s:%s>' % (self.domain, self.problem)

    def __hash__(self):
        return hash((self.domain, self.problem))

    def __cmp__(self, other):
        return cmp((self.domain, self.problem), (other.domain, other.problem))

    def problem_file(self):
        return os.path.join(self.benchmarks_dir, self.domain, self.problem)

    def domain_file(self):
        domain_basenames = [
            'domain.pddl',
            self.problem[:3] + '-domain.pddl',
            'domain_' + self.problem,
        ]
        domain_dir = os.path.join(self.benchmarks_dir, self.domain)
        return tools.find_file(domain_basenames, domain_dir)


def _generate_problems(benchmarks_dir, description):
    """
    Descriptions are either domains (e.g., "gripper") or problems
    (e.g., "gripper:prob01.pddl").
    """
    if isinstance(description, Problem):
        yield description
    elif isinstance(description, Domain):
        for problem in description:
            yield problem
    elif ':' in description:
        domain_name, problem_name = description.split(':', 1)
        yield Problem(benchmarks_dir, domain_name, problem_name)
    else:
        for problem in Domain(benchmarks_dir, description):
            yield problem


def build_suite(benchmarks_dir, descriptions):
    """
    *descriptions* must be a list of domain or problem descriptions::

        build_suite(benchmarks_dir, ["gripper", "grid:prob01.pddl"])

    """
    result = []
    for description in descriptions:
        result.extend(_generate_problems(benchmarks_dir, description))
    return result


def suite_alternative_formulations():
    return ['airport-adl', 'no-mprime', 'no-mystery']


def suite_ipc98_to_ipc04_adl():
    return [
        'assembly', 'miconic-fulladl', 'miconic-simpleadl',
        'optical-telegraphs', 'philosophers', 'psr-large',
        'psr-middle', 'schedule',
    ]


def suite_ipc98_to_ipc04_strips():
    return [
        'airport', 'blocks', 'depot', 'driverlog', 'freecell', 'grid',
        'gripper', 'logistics00', 'logistics98', 'miconic', 'movie',
        'mprime', 'mystery', 'pipesworld-notankage', 'psr-small',
        'satellite', 'zenotravel',
    ]


def suite_ipc98_to_ipc04():
    # All IPC1-4 domains, including the trivial Movie.
    return sorted(suite_ipc98_to_ipc04_adl() + suite_ipc98_to_ipc04_strips())


def suite_ipc06_adl():
    return [
        'openstacks',
        'pathways',
        'trucks',
    ]


def suite_ipc06_strips_compilations():
    return [
        'openstacks-strips',
        'pathways-noneg',
        'trucks-strips',
    ]


def suite_ipc06_strips():
    return [
        'pipesworld-tankage',
        'rovers',
        'storage',
        'tpp',
    ]


def suite_ipc06():
    return suite_ipc06_adl() + suite_ipc06_strips()


def suite_ipc08_common_strips():
    return [
        'parcprinter-08-strips',
        'pegsol-08-strips',
        'scanalyzer-08-strips',
    ]


def suite_ipc08_opt_strips():
    return suite_ipc08_common_strips() + [
        'elevators-opt08-strips',
        'openstacks-opt08-strips',
        'sokoban-opt08-strips',
        'transport-opt08-strips',
        'woodworking-opt08-strips',
    ]


def suite_ipc08_opt_adl():
    return ['openstacks-opt08-adl']


def suite_ipc08_opt():
    return suite_ipc08_opt_strips() + suite_ipc08_opt_adl()


def suite_ipc08_sat_strips():
    return suite_ipc08_common_strips() + [
        # Note: cyber-security is missing.
        'elevators-sat08-strips',
        'openstacks-sat08-strips',
        'sokoban-sat08-strips',
        'transport-sat08-strips',
        'woodworking-sat08-strips',
    ]


def suite_ipc08_sat_adl():
    return ['openstacks-sat08-adl']


def suite_ipc08_sat():
    return suite_ipc08_sat_strips() + suite_ipc08_sat_adl()


def suite_ipc08_all():
    return sorted(set(suite_ipc08_opt() + suite_ipc08_sat()))


def suite_ipc11_opt():
    return [
        'barman-opt11-strips',
        'elevators-opt11-strips',
        'floortile-opt11-strips',
        'nomystery-opt11-strips',
        'openstacks-opt11-strips',
        'parcprinter-opt11-strips',
        'parking-opt11-strips',
        'pegsol-opt11-strips',
        'scanalyzer-opt11-strips',
        'sokoban-opt11-strips',
        'tidybot-opt11-strips',
        'transport-opt11-strips',
        'visitall-opt11-strips',
        'woodworking-opt11-strips',
    ]


def suite_ipc11_sat():
    return [
        'barman-sat11-strips',
        'elevators-sat11-strips',
        'floortile-sat11-strips',
        'nomystery-sat11-strips',
        'openstacks-sat11-strips',
        'parcprinter-sat11-strips',
        'parking-sat11-strips',
        'pegsol-sat11-strips',
        'scanalyzer-sat11-strips',
        'sokoban-sat11-strips',
        'tidybot-sat11-strips',
        'transport-sat11-strips',
        'visitall-sat11-strips',
        'woodworking-sat11-strips',
    ]


def suite_ipc11():
    return suite_ipc11_opt() + suite_ipc11_sat()


def suite_unsolvable():
    # TODO: Add other unsolvable problems (Miconic-FullADL).
    # TODO: Add 'fsc-grid-r:prize5x5_R.pddl' and 't0-uts:uts_r-02.pddl'
    #       if the extra-domains branch is merged.
    return (['mystery:prob%02d.pddl' % index
             for index in [4, 5, 7, 8, 12, 16, 18, 21, 22, 23, 24]] +
            ['miconic-fulladl:f21-3.pddl', 'miconic-fulladl:f30-2.pddl'])


def suite_optimal_strips():
    # In addition to the domains in the old "suite_optimal_with_ipc11"
    # suite, this suite also contains "movie" and "storage".
    return sorted(
        suite_ipc98_to_ipc04_strips() + suite_ipc06_strips() +
        suite_ipc06_strips_compilations() + suite_ipc08_opt_strips() +
        suite_ipc11_opt())


@tools.deprecated(
    'suite_optimal_with_ipc11 is deprecated since version 1.10, please use '
    'suite_optimal_strips instead.')
def suite_optimal_with_ipc11():
    return suite_optimal_strips()


def suite_satisficing():
    domains = sorted(
        suite_ipc98_to_ipc04() + suite_ipc06() +
        suite_ipc06_strips_compilations() + suite_ipc08_sat() +
        suite_ipc11_sat())
    # Use pathways-noneg instead of pathways.
    domains.remove('pathways')
    return domains


@tools.deprecated(
    'suite_satisficing_with_ipc11 is deprecated since version 1.10, please use '
    'suite_satisficing instead.')
def suite_satisficing_with_ipc11():
    return suite_satisficing()


def suite_satisficing_strips():
    return sorted(
        suite_ipc98_to_ipc04_strips() + suite_ipc06_strips() +
        suite_ipc06_strips_compilations() + suite_ipc08_sat_strips() +
        suite_ipc11_sat())


def suite_all():
    return sorted(
        suite_ipc98_to_ipc04() + suite_ipc06() +
        suite_ipc06_strips_compilations() + suite_ipc08_all() +
        suite_ipc11() + suite_alternative_formulations())
