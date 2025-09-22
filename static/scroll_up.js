(function(){
    const btn = document.getElementById('toTopBtn');
    const SHOW_AFTER = 300; // px 이상 스크롤 시 표시

    const onScroll = () => {
      if (window.scrollY > SHOW_AFTER) btn.classList.add('show');
      else btn.classList.remove('show');
    };

    // 초기 상태 & 스크롤 감지
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    // 클릭 시 스무스 스크롤 (접근성: 모션 선호 고려)
    btn.addEventListener('click', () => {
      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
    });
  })();