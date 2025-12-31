#!/usr/bin/env python3
"""
Load Test Results Analyzer

Analyzes k6 JSON output and generates insights.

Usage:
    python analyze-results.py results.json
    python analyze-results.py results.json --type stress
    python analyze-results.py results.json --threshold-file thresholds.json
"""

import json
import sys
import argparse
from typing import Dict, Any, List
from pathlib import Path


class ResultsAnalyzer:
    """Analyze load test results"""

    def __init__(self, results_file: str, test_type: str = 'load'):
        self.results_file = Path(results_file)
        self.test_type = test_type
        self.results = self._load_results()
        self.metrics = self.results.get('metrics', {})

    def _load_results(self) -> Dict[str, Any]:
        """Load results from JSON file"""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Results file not found: {self.results_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in results file: {self.results_file}")
            sys.exit(1)

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive analysis"""
        analysis = {
            'summary': self._generate_summary(),
            'performance': self._analyze_performance(),
            'reliability': self._analyze_reliability(),
            'thresholds': self._check_thresholds(),
            'recommendations': self._generate_recommendations()
        }
        return analysis

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        http_reqs = self.metrics.get('http_reqs', {}).get('values', {})
        iterations = self.metrics.get('iterations', {}).get('values', {})
        vus = self.metrics.get('vus', {}).get('values', {})

        return {
            'test_type': self.test_type,
            'total_requests': http_reqs.get('count', 0),
            'request_rate': round(http_reqs.get('rate', 0), 2),
            'total_iterations': iterations.get('count', 0),
            'iteration_rate': round(iterations.get('rate', 0), 2),
            'peak_vus': vus.get('max', 0)
        }

    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics"""
        http_req_duration = self.metrics.get('http_req_duration', {}).get('values', {})
        http_req_waiting = self.metrics.get('http_req_waiting', {}).get('values', {})

        return {
            'response_times': {
                'avg': round(http_req_duration.get('avg', 0), 2),
                'min': round(http_req_duration.get('min', 0), 2),
                'med': round(http_req_duration.get('med', 0), 2),
                'max': round(http_req_duration.get('max', 0), 2),
                'p90': round(http_req_duration.get('p(90)', 0), 2),
                'p95': round(http_req_duration.get('p(95)', 0), 2),
                'p99': round(http_req_duration.get('p(99)', 0), 2),
            },
            'server_processing': {
                'avg': round(http_req_waiting.get('avg', 0), 2),
                'p95': round(http_req_waiting.get('p(95)', 0), 2),
            }
        }

    def _analyze_reliability(self) -> Dict[str, Any]:
        """Analyze reliability metrics"""
        http_req_failed = self.metrics.get('http_req_failed', {}).get('values', {})
        checks = self.metrics.get('checks', {}).get('values', {})

        failure_rate = http_req_failed.get('rate', 0) * 100
        check_rate = checks.get('rate', 1) * 100

        return {
            'error_rate': round(failure_rate, 2),
            'success_rate': round(100 - failure_rate, 2),
            'checks_passed': round(check_rate, 2),
            'reliability_score': self._calculate_reliability_score(failure_rate, check_rate)
        }

    def _calculate_reliability_score(self, failure_rate: float, check_rate: float) -> str:
        """Calculate overall reliability score"""
        if failure_rate < 1 and check_rate > 99:
            return 'EXCELLENT'
        elif failure_rate < 5 and check_rate > 95:
            return 'GOOD'
        elif failure_rate < 10 and check_rate > 90:
            return 'ACCEPTABLE'
        else:
            return 'POOR'

    def _check_thresholds(self) -> Dict[str, Any]:
        """Check if thresholds passed"""
        threshold_results = {}
        all_passed = True

        for metric_name, metric_data in self.metrics.items():
            thresholds = metric_data.get('thresholds', {})
            if thresholds:
                for threshold_name, threshold_result in thresholds.items():
                    passed = threshold_result.get('ok', True)
                    threshold_results[f"{metric_name}:{threshold_name}"] = {
                        'passed': passed,
                        'value': threshold_result.get('value')
                    }
                    if not passed:
                        all_passed = False

        return {
            'all_passed': all_passed,
            'results': threshold_results
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on results"""
        recommendations = []
        perf = self._analyze_performance()
        rel = self._analyze_reliability()

        # Response time recommendations
        p95 = perf['response_times']['p95']
        if p95 > 1000:
            recommendations.append(
                f"⚠️  P95 response time is {p95}ms. Consider optimizing slow endpoints."
            )
        elif p95 > 500:
            recommendations.append(
                f"ℹ️  P95 response time is {p95}ms. Monitor for degradation."
            )
        else:
            recommendations.append(
                f"✅ P95 response time is {p95}ms. Performance is good."
            )

        # Error rate recommendations
        error_rate = rel['error_rate']
        if error_rate > 5:
            recommendations.append(
                f"❌ Error rate is {error_rate}%. Investigate failing requests."
            )
        elif error_rate > 1:
            recommendations.append(
                f"⚠️  Error rate is {error_rate}%. Monitor for issues."
            )
        else:
            recommendations.append(
                f"✅ Error rate is {error_rate}%. Reliability is good."
            )

        # Check rate recommendations
        check_rate = rel['checks_passed']
        if check_rate < 90:
            recommendations.append(
                f"❌ Only {check_rate}% of checks passed. Review failing assertions."
            )
        elif check_rate < 98:
            recommendations.append(
                f"⚠️  {check_rate}% of checks passed. Some assertions failing."
            )

        # Max response time
        max_time = perf['response_times']['max']
        if max_time > 10000:
            recommendations.append(
                f"⚠️  Maximum response time is {max_time}ms. Investigate outliers."
            )

        return recommendations

    def print_report(self):
        """Print formatted analysis report"""
        analysis = self.analyze()

        print("=" * 60)
        print("LOAD TEST ANALYSIS REPORT")
        print("=" * 60)

        # Summary
        print("\nSUMMARY")
        print("-" * 60)
        summary = analysis['summary']
        print(f"Test Type:        {summary['test_type']}")
        print(f"Total Requests:   {summary['total_requests']}")
        print(f"Request Rate:     {summary['request_rate']} req/s")
        print(f"Total Iterations: {summary['total_iterations']}")
        print(f"Peak VUs:         {summary['peak_vus']}")

        # Performance
        print("\nPERFORMANCE")
        print("-" * 60)
        perf = analysis['performance']
        rt = perf['response_times']
        print(f"Avg Response Time: {rt['avg']}ms")
        print(f"Min Response Time: {rt['min']}ms")
        print(f"Med Response Time: {rt['med']}ms")
        print(f"Max Response Time: {rt['max']}ms")
        print(f"P90 Response Time: {rt['p90']}ms")
        print(f"P95 Response Time: {rt['p95']}ms")
        print(f"P99 Response Time: {rt['p99']}ms")

        # Reliability
        print("\nRELIABILITY")
        print("-" * 60)
        rel = analysis['reliability']
        print(f"Success Rate:     {rel['success_rate']}%")
        print(f"Error Rate:       {rel['error_rate']}%")
        print(f"Checks Passed:    {rel['checks_passed']}%")
        print(f"Reliability Score: {rel['reliability_score']}")

        # Thresholds
        print("\nTHRESHOLDS")
        print("-" * 60)
        thresholds = analysis['thresholds']
        if thresholds['all_passed']:
            print("✅ All thresholds PASSED")
        else:
            print("❌ Some thresholds FAILED")
            print("\nFailed Thresholds:")
            for name, result in thresholds['results'].items():
                if not result['passed']:
                    print(f"  - {name}")

        # Recommendations
        print("\nRECOMMENDATIONS")
        print("-" * 60)
        for rec in analysis['recommendations']:
            print(f"  {rec}")

        print("=" * 60)

        # Exit code based on thresholds
        return 0 if thresholds['all_passed'] else 1


def main():
    parser = argparse.ArgumentParser(description='Analyze load test results')
    parser.add_argument('results_file', help='Path to k6 JSON results file')
    parser.add_argument('--type', default='load', help='Test type (smoke, load, stress)')
    parser.add_argument('--output', help='Output file for JSON analysis')

    args = parser.parse_args()

    analyzer = ResultsAnalyzer(args.results_file, args.type)
    exit_code = analyzer.print_report()

    # Save JSON output if requested
    if args.output:
        analysis = analyzer.analyze()
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\nAnalysis saved to: {args.output}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
