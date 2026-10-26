interface Props {
  panelOpen: boolean;
}

/**
 * "맨 위로" 버튼. 분석 카드(최대 너비 896px, 가운데 정렬)의 오른쪽 바깥에 12px 띄워 붙는다.
 * - 패널이 닫혀 있으면: 카드 오른쪽 끝 = 화면 가운데 + 448px
 * - 패널이 열려 있으면(큰 화면): 카드가 패널 폭(400px)만큼 왼쪽으로 밀려 오른쪽 끝 = 화면 가운데 + 256px
 * 화면이 좁아 카드 옆에 자리가 없으면 화면(또는 패널) 안쪽 끝에 멈춘다.
 */
export default function ScrollTopButton({ panelOpen }: Props) {
  return (
    <button
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      aria-label="맨 위로"
      title="맨 위로"
      className={`fixed bottom-6 z-10 flex h-11 w-11 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 shadow-md transition-[left] duration-300 hover:bg-slate-50 hover:text-slate-900 left-[min(calc(50%_+_460px),calc(100%_-_60px))] ${
        panelOpen ? "lg:left-[min(calc(50%_+_268px),calc(100%_-_440px))]" : ""
      }`}
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 19V5M5 12l7-7 7 7" />
      </svg>
    </button>
  );
}
