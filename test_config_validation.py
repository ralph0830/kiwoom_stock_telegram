"""
config.py 검증 테스트

목적:
- TradingConfig 클래스 구조 확인
- 환경변수 로드 검증
- 필수 필드 존재 확인
- 타입 및 값 검증
- validate() 메서드 동작 확인
"""

import os
import logging
from datetime import datetime
from config import TradingConfig

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_config_load():
    """환경변수에서 Config 로드 테스트"""
    logger.info("=" * 80)
    logger.info("🧪 테스트 1: 환경변수에서 Config 로드")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()
        logger.info("✅ Config 로드 성공")

        # 필수 필드 확인
        logger.info("\n📋 필수 계좌 정보:")
        logger.info(f"   account_no: {config.account_no}")
        logger.info(f"   max_investment: {config.max_investment:,}원")

        logger.info("\n📋 수익률 설정:")
        logger.info(f"   target_profit_rate: {config.target_profit_rate*100:.2f}% (소수: {config.target_profit_rate})")
        logger.info(f"   stop_loss_rate: {config.stop_loss_rate*100:.2f}% (소수: {config.stop_loss_rate})")
        logger.info(f"   stop_loss_delay_minutes: {config.stop_loss_delay_minutes}분")

        logger.info("\n📋 매수 시간 설정:")
        logger.info(f"   buy_start_time: {config.buy_start_time}")
        logger.info(f"   buy_end_time: {config.buy_end_time}")

        logger.info("\n📋 매도 설정:")
        logger.info(f"   enable_sell_monitoring: {config.enable_sell_monitoring}")
        logger.info(f"   enable_stop_loss: {config.enable_stop_loss}")
        logger.info(f"   enable_daily_force_sell: {config.enable_daily_force_sell}")
        logger.info(f"   daily_force_sell_time: {config.daily_force_sell_time}")

        logger.info("\n📋 미체결 처리 설정:")
        logger.info(f"   cancel_outstanding_on_failure: {config.cancel_outstanding_on_failure}")
        logger.info(f"   outstanding_check_timeout: {config.outstanding_check_timeout}초")
        logger.info(f"   outstanding_check_interval: {config.outstanding_check_interval}초")

        logger.info("\n📋 체결 검증 설정:")
        logger.info(f"   enable_lazy_verification: {config.enable_lazy_verification}")

        logger.info("\n📋 주기적 계좌 조회 설정:")
        logger.info(f"   balance_check_interval: {config.balance_check_interval}초")

        logger.info("\n📋 매수 주문 타입 설정 (v1.6.0):")
        logger.info(f"   buy_order_type: {config.buy_order_type}")
        logger.info(f"   buy_execution_timeout: {config.buy_execution_timeout}초")
        logger.info(f"   buy_execution_check_interval: {config.buy_execution_check_interval}초")
        logger.info(f"   buy_fallback_to_market: {config.buy_fallback_to_market}")

        logger.info("\n📋 디버그 모드:")
        logger.info(f"   debug_mode: {config.debug_mode}")

        logger.info("\n📋 Telegram 설정 (선택적):")
        logger.info(f"   api_id: {config.api_id}")
        logger.info(f"   api_hash: {'*' * 10 if config.api_hash else None}")
        logger.info(f"   session_name: {config.session_name}")
        logger.info(f"   source_channel: {config.source_channel}")
        logger.info(f"   target_channel: {config.target_channel if config.target_channel else '(비활성화)'}")

        return True

    except Exception as e:
        logger.error(f"❌ Config 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Config validate() 메서드 테스트"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 2: Config validate() 메서드")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()
        config.validate()
        logger.info("✅ Config 검증 통과")
        return True

    except ValueError as e:
        logger.error(f"❌ Config 검증 실패: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_types():
    """Config 필드 타입 검증"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 3: Config 필드 타입 검증")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()

        # 타입 검증
        type_checks = [
            ("account_no", str, config.account_no),
            ("max_investment", int, config.max_investment),
            ("target_profit_rate", float, config.target_profit_rate),
            ("stop_loss_rate", float, config.stop_loss_rate),
            ("stop_loss_delay_minutes", int, config.stop_loss_delay_minutes),
            ("buy_start_time", str, config.buy_start_time),
            ("buy_end_time", str, config.buy_end_time),
            ("enable_sell_monitoring", bool, config.enable_sell_monitoring),
            ("enable_stop_loss", bool, config.enable_stop_loss),
            ("enable_daily_force_sell", bool, config.enable_daily_force_sell),
            ("daily_force_sell_time", str, config.daily_force_sell_time),
            ("cancel_outstanding_on_failure", bool, config.cancel_outstanding_on_failure),
            ("outstanding_check_timeout", int, config.outstanding_check_timeout),
            ("outstanding_check_interval", int, config.outstanding_check_interval),
            ("enable_lazy_verification", bool, config.enable_lazy_verification),
            ("balance_check_interval", int, config.balance_check_interval),
            ("buy_order_type", str, config.buy_order_type),
            ("buy_execution_timeout", int, config.buy_execution_timeout),
            ("buy_execution_check_interval", int, config.buy_execution_check_interval),
            ("buy_fallback_to_market", bool, config.buy_fallback_to_market),
            ("debug_mode", bool, config.debug_mode),
        ]

        all_passed = True
        for field_name, expected_type, value in type_checks:
            if isinstance(value, expected_type):
                logger.info(f"   ✅ {field_name}: {expected_type.__name__} (값: {value})")
            else:
                logger.error(f"   ❌ {field_name}: 예상 타입={expected_type.__name__}, 실제 타입={type(value).__name__}, 값={value}")
                all_passed = False

        return all_passed

    except Exception as e:
        logger.error(f"❌ 타입 검증 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_values():
    """Config 값 유효성 검증"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 4: Config 값 유효성 검증")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()

        all_passed = True

        # 1. account_no 형식 (12345678-01)
        if "-" in config.account_no:
            logger.info(f"   ✅ account_no 형식: {config.account_no}")
        else:
            logger.error(f"   ❌ account_no 형식 오류: {config.account_no}")
            all_passed = False

        # 2. max_investment > 0
        if config.max_investment > 0:
            logger.info(f"   ✅ max_investment: {config.max_investment:,}원 (> 0)")
        else:
            logger.error(f"   ❌ max_investment: {config.max_investment} (<= 0)")
            all_passed = False

        # 3. target_profit_rate > 0
        if config.target_profit_rate > 0:
            logger.info(f"   ✅ target_profit_rate: {config.target_profit_rate*100:.2f}% (> 0)")
        else:
            logger.error(f"   ❌ target_profit_rate: {config.target_profit_rate*100:.2f}% (<= 0)")
            all_passed = False

        # 4. stop_loss_rate < 0
        if config.stop_loss_rate < 0:
            logger.info(f"   ✅ stop_loss_rate: {config.stop_loss_rate*100:.2f}% (< 0)")
        else:
            logger.error(f"   ❌ stop_loss_rate: {config.stop_loss_rate*100:.2f}% (>= 0)")
            all_passed = False

        # 5. 시간 형식 (HH:MM)
        time_fields = [
            ("buy_start_time", config.buy_start_time),
            ("buy_end_time", config.buy_end_time),
            ("daily_force_sell_time", config.daily_force_sell_time)
        ]

        for field_name, time_str in time_fields:
            try:
                parts = time_str.split(":")
                if len(parts) == 2:
                    hour, minute = int(parts[0]), int(parts[1])
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        logger.info(f"   ✅ {field_name}: {time_str} (HH:MM 형식)")
                    else:
                        logger.error(f"   ❌ {field_name}: {time_str} (시간 범위 오류)")
                        all_passed = False
                else:
                    logger.error(f"   ❌ {field_name}: {time_str} (형식 오류)")
                    all_passed = False
            except Exception as e:
                logger.error(f"   ❌ {field_name}: {time_str} (파싱 오류: {e})")
                all_passed = False

        # 6. buy_order_type 값 확인
        if config.buy_order_type in ["market", "limit_plus_one_tick"]:
            logger.info(f"   ✅ buy_order_type: {config.buy_order_type}")
        else:
            logger.error(f"   ❌ buy_order_type: {config.buy_order_type} (유효하지 않은 값)")
            all_passed = False

        # 7. timeout/interval > 0
        if config.outstanding_check_timeout > 0:
            logger.info(f"   ✅ outstanding_check_timeout: {config.outstanding_check_timeout}초")
        else:
            logger.error(f"   ❌ outstanding_check_timeout: {config.outstanding_check_timeout}초 (<= 0)")
            all_passed = False

        if config.outstanding_check_interval > 0:
            logger.info(f"   ✅ outstanding_check_interval: {config.outstanding_check_interval}초")
        else:
            logger.error(f"   ❌ outstanding_check_interval: {config.outstanding_check_interval}초 (<= 0)")
            all_passed = False

        return all_passed

    except Exception as e:
        logger.error(f"❌ 값 검증 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_str():
    """Config __str__() 메서드 테스트"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 5: Config __str__() 메서드")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()
        config_str = str(config)

        logger.info("\n" + config_str)
        logger.info("✅ Config __str__() 정상 동작")
        return True

    except Exception as e:
        logger.error(f"❌ __str__() 호출 실패: {e}")
        return False


def test_env_missing_fields():
    """필수 환경변수 누락 테스트"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 6: 필수 환경변수 누락 처리")
    logger.info("=" * 80)

    # ACCOUNT_NO 백업 및 삭제
    original_account_no = os.getenv("ACCOUNT_NO")

    try:
        # ACCOUNT_NO 삭제
        if "ACCOUNT_NO" in os.environ:
            del os.environ["ACCOUNT_NO"]

        try:
            config = TradingConfig.from_env(load_dotenv_first=False)
            logger.error("❌ ACCOUNT_NO 누락 시 ValueError가 발생해야 하는데 발생하지 않음")
            return False
        except ValueError as e:
            logger.info(f"✅ 필수 환경변수 누락 시 ValueError 발생: {e}")
            return True

    finally:
        # ACCOUNT_NO 복원
        if original_account_no:
            os.environ["ACCOUNT_NO"] = original_account_no


def main():
    """메인 테스트 실행"""
    logger.info("=" * 80)
    logger.info("🧪 config.py 검증 테스트 시작")
    logger.info("=" * 80)
    logger.info("")

    results = []

    # 테스트 1: 환경변수 로드
    results.append(("환경변수 로드", test_config_load()))

    # 테스트 2: validate() 메서드
    results.append(("validate() 메서드", test_config_validation()))

    # 테스트 3: 타입 검증
    results.append(("필드 타입 검증", test_config_types()))

    # 테스트 4: 값 유효성 검증
    results.append(("값 유효성 검증", test_config_values()))

    # 테스트 5: __str__() 메서드
    results.append(("__str__() 메서드", test_config_str()))

    # 테스트 6: 필수 환경변수 누락
    results.append(("필수 환경변수 누락 처리", test_env_missing_fields()))

    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("📊 테스트 결과 요약")
    logger.info("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {status} | {test_name}")

    logger.info("\n" + "=" * 80)
    if passed == total:
        logger.info(f"✅ 모든 테스트 통과! ({passed}/{total})")
    else:
        logger.error(f"❌ 일부 테스트 실패 ({passed}/{total})")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
